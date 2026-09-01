# Tunele pakietów B i E — ta sama poprzeczka co pakiet A

Stan: **2026-09-01**. Wariant: **`flat-preview`, nieprodukcyjny** — osie
`data/track/L1_B.json` i `data/track/L2_E.json` mają `vertical.status =
"not_modelled"`, cała geometria leży na Z = 0, generator odmawia wariantu
`production` do zamknięcia T-112 (#10).

Ten raport opisuje **wyłącznie różnice, rozstrzygnięcia i zmierzone liczby**.
Metoda, uzasadnienie chunków, LOD-ów i bryły kolizyjnej są w
`reports/L1_A-geometry.md`, `reports/L1_A-chunks.md` i `reports/L1_A-lod.md`
i nie powtarzam ich tutaj.

---

## 1. Dlaczego akurat B i E

Z `reports/surface-vs-tunnel.md` §3, gdzie każdy punkt sześciu osi jest
sklasyfikowany przez **dwa niezależne źródła**:

| pakiet | punktów poza tunelem (OSM) | punktów, gdzie UrbIS zawyża tunel | zbudowany jako rura |
|---|---:|---:|---|
| A — Pień 1/5 | 1,8 % | **0** | tak, wcześniej (#12) |
| B — Wschód 1 | **0,0 %** | **0** | **tak, tutaj** |
| C — Zachód 5 | 8,6 % | **0** | nie — decyzja właściciela |
| D — Wschód 5 | 69,8 % | 48 | nie |
| E — Pierścień 2/6 | 2,7 % | **0** | **tak, tutaj** |
| F — Północ 6 | 22,7 % | 33 | nie |

Kryterium jest jedno i jest mierzalne: **żadne z dwóch źródeł nie stawia
zamkniętej rury na odcinku, którego nie ma.** Kolumna „UrbIS zawyża tunel" liczy
punkty, w których UrbIS mówi `niveau ≠ 0`, a OSM nie widzi tagu `tunnel` — czyli
dokładnie te miejsca, gdzie generator zbudowałby ścianę wokół otwartego nieba.
W A, B, C i E jest ich zero.

Pakiet **C nie wchodzi** mimo zerowej kolumny sprzeczności: 449 m poza tunelem to
8,6 % osi i to jest próg, którego nie przekraczam bez decyzji właściciela.
**D i F** czekają na model odcinka poza tunelem, którego nie ma ani w `data/`,
ani w `docs/`.

### Co jest świadomie nieprawdziwe w tych dwóch tunelach

| pakiet | kilometraż | co tam naprawdę jest | ile |
|---|---|---|---:|
| B | — | — | 0 m |
| E | 7762–7867 m, 7897–7927 m | estakada Delacroix – Clemenceau, OSM `layer = 1` | 135 m |
| E | 8556–8616 m | odcinek poza tunelem tuż za Gare de l'Ouest | 60 m |

Razem **195 m z 9021 m pakietu E, czyli 2,2 %** jest zbudowane jako zamknięta
rura, choć nie jest tunelem. Pakiet A ma tego 90 m z 6686 m (1,3 %). Nic tego nie
ukrywa: przedziały są wypisane wyżej i w `reports/surface-vs-tunnel.md`, a
`data/track/*.json` niesie `vertical.status = "not_modelled"`, więc żaden z tych
tuneli i tak nie może wyjść jako `production`.

## 2. Uruchomienie

`tools/ci/tunnel_alignment.sh` bierze teraz **identyfikator osi jako argument**.
Pakiet A nie jest w niczym wyróżniony; artefakty idą do `build/t210/<ID>/`:

```bash
bash tools/ci/tunnel_alignment.sh L1_A
bash tools/ci/tunnel_alignment.sh L1_B
bash tools/ci/tunnel_alignment.sh L2_E
```

Workflow `.github/workflows/tunnel-alignment.yml` jest teraz macierzą po tych
trzech osiach, z `fail-fast: false` — porażka jednego pakietu nie ma anulować
pozostałych, bo interesuje nas, czy to jeden pakiet, czy cała generacja.

## 3. Wynik — trzy pakiety, ta sama poprzeczka

| | A (Pień 1/5) | B (Wschód 1) | E (Pierścień 2/6) |
|---|---:|---:|---:|
| oś [m] | 6686,739 | 5083,479 | 9021,052 |
| łamana źródłowa [m] | 6686,354 | 5083,233 | 9020,771 |
| stacji | 12 | 9 | 17 |
| chunków | 12 | 9 | 17 |
| trójkątów (LOD 0) | 16 176 | 12 288 | 21 852 |
| wierzchołków | 9 520 | 7 231 | 12 866 |
| pliki chunków [B] | 892 756 | 694 800 | 1 215 676 |
| **szczelina między chunkami** | **0,0000 mm** | **0,0000 mm** | **0,0000 mm** |
| **szczelina między LOD-ami** | **0,0000 mm** | **0,0000 mm** | **0,0000 mm** |
| **szczelina bryły kolizyjnej** | **0,0000 mm** | **0,0000 mm** | **0,0000 mm** |
| **normalnych na zewnątrz rury** | **0** | **0** | **0** |
| **ścian zdegenerowanych** | **0** | **0** | **0** |
| **wierzchołków NaN/Inf** | **0** | **0** | **0** |
| szwów na peronie | **0** | **0** | **0** |
| skręt ramki [°] | 0,0 | 0,0 | 0,0 |
| błąd wygładzenia [m] | 0,2499 | 0,1733 | 0,2166 |
| gęstość UV [m/jednostkę] | 3,80–4,20 | 3,86–4,14 | 3,82–4,18 |
| bryła kolizyjna zamknięta | tak | tak | tak |
| zapas kolizji do ściany [m] | 0,0536 | 0,0512 | 0,0521 |
| zapas kolizji do skrajni [m] | 0,650 | 0,650 | 0,650 |
| streaming: maks. chunków naraz | 4 z 12 | **3 z 9** | 4 z 17 |
| LOD: szczyt trójkątów wobec pełnej rozdzielczości | 70,9 % | 71,3 % | 76,4 % |

Determinizm: drugi przebieg dał **identyczną geometrię we wszystkich chunkach**
(`geometry_sha256`) w każdym z trzech pakietów. Round-trip GLB każdego chunka,
każdego poziomu LOD i bryły kolizyjnej przeszedł. Kontrole negatywne
(przekręcony bajt w pliku chunka, przekręcony bajt w LOD 2, zepsuty zakres
chainage w manifeście) wykryły uszkodzenie w każdym pakiecie — kontrola, która
przechodzi tylko na poprawnym wejściu, nie dowodzi niczego.

### Skrajnia M7 na rzeczywistych łukach

| | A | B | E |
|---|---:|---:|---:|
| luz statyczny do ściany [m] | 1,078 | 1,078 | 1,078 |
| najciaśniejszy R (widełki pesymistyczne) [m] | 50,87 | 73,97 | 59,13 |
| zapas w najgorszym punkcie [m] | **0,4713** | **0,6621** | **0,5568** |
| zapas w widełkach optymistycznych [m] | 0,7203 | 0,8211 | 0,7564 |

Skład mieści się na każdym łuku każdego z trzech pakietów. **Najciaśniejszy jest
pakiet A**, nie nowe — pakiety B i E mają większy zapas niż ten już zbudowany.

## 4. Co widać na renderach

Obejrzane, nie opisane z metryk.

**`L1_B_plan`** — ciągła oś od Montgomery na wschód, z łagodnym S na początku
i wyraźnym zakolem przed końcem. Ani jednego przerwania, samoprzecięcia czy
odcinka zwiniętego w punkt.

**`L2_E_plan`** — pierścień. Widać, że oś **nie domyka się**: koniec (Beekkant)
i początek (Elisabeth) to dwa osobne końce w lewym górnym rogu, oddalone od
siebie. Tak ma być — pakiet E jest wycinkiem pierścienia od Elisabeth do
Beekkant, a nie zamkniętą pętlą.

**`L1_B_axis50` i `L2_E_axis25`** — widok z wnętrza rury wzdłuż osi. Pierścienie
co 5 m ciągną się w głąb bez ani jednej przerwy, ściany są widoczne **od
środka** (nie widać „przez" nie), a przekrój ma ścięte górne naroża profilu
`box_double`. W obu tunel skręca w prawo — to jest rzeczywisty łuk osi, nie
artefakt.

**`L1_B_section` i `L2_E_section`** — obrys przekroju: prostokąt 9,40 × 5,90 m ze
ściętymi górnymi narożami. Jeden obrys, nie dwa — kadr nie łapie drugiej strony
pierścienia (patrz §5).

**`L1_A_side`, `L1_B_side`, `L2_E_side`** — elewacja boczna 80-metrowego odcinka:
pasek wysokości 5,90 m z pionowymi kreskami pierścieni co 5 m i przekątnymi
triangulacji. Góra i dół są **idealnie poziome** na całej długości — i tak ma
być, dopóki `vertical.status = "not_modelled"`. To jest ten render, na którym
zobaczy się niweletę, kiedy T-112 ją dostarczy.

**`CHUNK_axis50` pakietu B** — pojedynczy chunk od środka: pierścienie co 5 m,
zamknięta rura, brak uskoku na szwie.

**`LOD2_axis50` pakietu B** — ten sam chunk w najrzadszej siatce: pierścienie co
kilkadziesiąt metrów, rura wyraźnie „ścięta" na cięciwach. Ubytek jest widoczny
gołym okiem i zgadza się ze zmierzonym `blad_max = 0,41 m` dla poziomu 2.

**`COL_section` pakietu B** — obrys bryły kolizyjnej: ten sam kształt, mniejszy
o wcięcie. Zmierzone `wciecie = 0,15 m`, co widać jako równomierny odstęp od
obrysu tunelu.

## 5. Błędy znalezione przez uogólnienie — i dlaczego pakiet A ich nie pokazał

To jest właściwa treść tego zadania. Pakiet A przechodził wszystkie cztery
kontrole poniżej **przypadkiem**, nie dlatego, że były poprawne.

### 5.1 Manifest odrzucany na samym zaokrągleniu

```
BŁĄD: manifest niespójny — L2_E_flat_preview_c08: length_m 539.477855 != 539.4778560000004;
      L2_E_flat_preview_c11: length_m 424.571317 != 424.57131800000025;
      L2_E_flat_preview_c12: length_m 569.43332 != 569.4333189999998
```

`length_m` było zaokrąglane **niezależnie** od `start_m` i `end_m`. Dla liczb, na
których `round(b, 6) - round(a, 6)` i `round(b - a, 6)` rozjeżdżają się o 1e-6 —
czyli dokładnie o tolerancję szwu — kontrola słusznie zgłaszała niespójny
manifest przy poprawnej geometrii. **Pięć z siedemnastu chunków pakietu E** trafia
w ten przypadek; pakiet A nie trafia w niego ani razu.

Naprawa: `sweep.manifest_span()` liczy długość **z już zaokrąglonych końców**, więc
trójka (start, koniec, długość) jest spójna z definicji. Regresja stoi na
prawdziwych liczbach chunków c08 i c12, po jednym przypadku w każdą stronę.

### 5.2 Przekrój LOD 2 kadrowany na bboxie całego chunka

Płat +-12 m wokół kotwicy zakłada pierścienie co kilka metrów. Na LOD 2 stoją co
kilkadziesiąt i płat bywa **pusty** — kadr cicho spadał wtedy na bbox całego
chunka i przekrój 9,4 × 5,9 m lądował jako plamka na 570-metrowej klatce
(`ink = 0.0000`). Naprawa jest dwuczęściowa:

- płat **rośnie**, aż złapie geometrię (do sześciu podwojeń), a użyta grubość
  trafia do metadanych jako `slab_thickness_used_m` — na chunku pakietu E wyszło
  **48 m**, na pakiecie B wystarczyło 12 m;
- `tools/ci/tunnel_alignment.sh` **wywraca się** na `fit_fallback` w metadanych.
  Wykrywanie kadru zastępczego przez „obraz jest jednorodny" było zgadywanką;
  metadane mówią to wprost.

### 5.3 Przekrój pierścienia obejmował drugą stronę pierścienia

Na pełnej osi pakietu E płaszczyzna cięcia przecina trasę **dwa razy**, bo trasa
zawraca. `ortho_scale` rosło z 16,5 m do **4777,7 m**: kadr formalnie „znajdował
geometrię", a pokazywał pustkę. Naprawa: `slab_radius_m = 40 m` odrzuca punkty
leżące w płaszczyźnie cięcia, ale dalej w bok niż promień. Po zmianie E daje
16,645 m, czyli tyle samo, co A (16,542 m) i B (16,715 m).

### 5.4 Kamera `side` była rzutem monetą, nie kontrolą

Na pojedynczym chunku `side` patrzy na 500-metrową rurę z boku i widzi pasek
jednolitej szarości. Czy ten pasek ma w sobie czarny prostokąt otwartego wylotu,
zależy **wyłącznie od azymutu chunka**: zmierzone, chunk pakietu A daje 67
poziomów jasności i przechodzi, chunk pakietu E daje 7 i jest odrzucany — obie
siatki są poprawne. Kontrola, której wynik zależy od azymutu, a nie od geometrii,
nie jest kontrolą.

Na **pełnej osi** było jeszcze gorzej: bez ograniczenia głębi kamera całkowała
27–43 km ściany w jednolity pasek. Naprawa jest inna dla każdej skali:

- pełna oś: `depth_m = 60 m` + siatka drutowa. Kadr pokazuje teraz **elewację
  80-metrowego odcinka** z pierścieniami co 5 m — czyli to, co ta kamera miała
  pokazywać według swojego wpisu w manifeście od początku;
- pojedynczy chunk: `side` **nie jest oceniana**. Renderuje się jako artefakt,
  ale nie orzeka, bo na tej skali nie odpowiada na żadne pytanie.

## 6. Weryfikacja

```
$ bash tools/ci/tunnel_alignment.sh L1_A   ->  exit=0
$ bash tools/ci/tunnel_alignment.sh L1_B   ->  exit=0
$ bash tools/ci/tunnel_alignment.sh L2_E   ->  exit=0

$ python3 tools/tests/test_all.py
  364/364 przeszło
```

Trzy nowe testy w `tools/tests/test_chunks.py` (spójność trójki start/koniec/
długość na prawdziwych liczbach pakietu E, plus negatyw) i trzy w
`tools/tests/test_visual.py` (rosnący płat, kadr zastępczy przy braku geometrii,
promień płata na trasie zawracającej).

## 7. Czego świadomie nie zrobiono

- **Nie zbudowano C, D ani F.** Powody i liczby w §1.
- **Nie ruszono `data/`.** Osie B i E są takie, jakie weszły w #68.
- **Nie policzono profilu luzu wzdłuż całych osi B i E** — `clearance.py` daje
  najgorszy punkt, a pełny profil (jak `reports/M7-clearance-profile.md` dla
  pakietu A) to osobne zadanie.
- **Nie sprawdzono ciągłości kilometrażu między pakietami.** Manifest jest per
  pakiet, nie per linia; osie B i E stykają się z A odpowiednio w Montgomery
  i Beekkant, ale nikt tego nie zmierzył.
- **Nie zmieniono profilu `box_double`.** Wymiary są `design_assumption`
  (`docs/21-measured-vs-assumed.md`) i należą do R-005 (#17).
