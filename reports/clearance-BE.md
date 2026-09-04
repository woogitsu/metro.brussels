# Profil luzu M7 wzdłuż osi pakietów B i E

**Zmierzone na commicie:** `1b7c2bb`

Stan: **2026-09-01**. Narzędzia: `tools/ci/vehicle_clearance.sh <ID_OSI>`,
`tools/blender/place_vehicle.py`, `tools/blender/profile_vehicle.py`.
Wariant tuneli: **`flat-preview`, nieprodukcyjny** (Z = 0, T-112 zablokowane).

Metoda jest w `reports/M7-clearance-profile.md` i nie powtarzam jej tutaj. Ten raport
podaje **liczby dla trzech pakietów** i opisuje błąd, który uogólnienie wywlekło —
ten sam co w E1.2, tylko schowany w trzech kopiach naraz.

---

## 1. Wynik — najciaśniejszy jest pakiet A, nie nowe

Skład M7 przesuwany co 5 m wzdłuż całej osi, oba tory, z doszlifowaniem krokiem
0,25 m w oknach wokół dołków.

| | A — Pień 1/5 | B — Wschód 1 | E — Pierścień 2/6 |
|---|---:|---:|---:|
| oś [m] | 6686,7 | 5083,5 | 9021,1 |
| pozycji na tor | 1320 | 999 | 1787 |
| **minimum, tor 0** [m] | 0,9189 | **0,9981** | 0,9481 |
| **minimum, tor 1** [m] | **0,8999** | 1,0196 | 0,9353 |
| mediana obu torów [m] | 1,1000 | 1,1000 | 1,1000 |
| pozycji < 1,000 m (t0 / t1) | 33 / 57 | **0 / 0** | 17 / 38 |
| pozycji < 0,950 m (t0 / t1) | 28 / 34 | **0 / 0** | 0 / 6 |
| pozycji < 0,900 m | **0** | **0** | **0** |
| pozycji z luzem ujemnym | **0** | **0** | **0** |

**Nigdzie, w żadnym z trzech pakietów, na żadnym torze, skład nie wchodzi w obrys
tunelu.** Najciaśniej jest w pakiecie A — tym już zbudowanym — a nie w nowych.

Mediana 1,1000 m na obu torach każdego pakietu to nie zbieg okoliczności: na prostej
i na łagodnym łuku wiąże **ścięcie naroża stropu** na wysokości 3,60 m, a nie ściana
boczna. Ta wartość nie zależy od promienia, więc jest identyczna wszędzie tam, gdzie
łuk nie jest dość ostry, żeby wypchnąć pudło do ściany.

### Gdzie robi się ciasno

| pakiet | tor | kilometraż | luz [m] | wiąże | najbliższa stacja |
|---|---:|---:|---:|---|---|
| A | 0 | 2786,2 | 0,9189 | ściana | Sainte-Catherine +65 m |
| A | 1 | **2521,1** | **0,8999** | ściana | Sainte-Catherine +200 m |
| A | 1 | 3405,6 | 0,9147 | ściana | De Brouckère +275 m |
| A | 1 | 946,4 | 0,9910 | ściana | Beekkant +437 m |
| B | 0 | 27,6 | 0,9981 | ściana | Montgomery +28 m |
| E | 0 | 8584,1 | 0,9481 | ściana | Gare de l'Ouest +71 m |
| E | 1 | **4288,1** | **0,9353** | ściana | Trône +61 m |
| E | 1 | 6036,7 | 0,9405 | ściana | Porte de Hal +129 m |
| E | 1 | 2815,5 | 0,9979 | ściana | Botanique +209 m |
| E | 1 | 8393,5 | 0,9987 | ściana | Gare de l'Ouest +119 m |

Wszystkie dołki wiąże **ściana**, żaden strop — czyli wszystkie biorą się z łuku,
nie z wysokości profilu.

**Jedna uwaga, której nie wolno pominąć.** Najciaśniejsze miejsce toru 0 pakietu E
(kilometraż 8584,1 m) leży w przedziale **8556–8616 m**, o którym
`reports/surface-vs-tunnel.md` mówi, że **nie jest tunelem**. Luz 0,9481 m jest tam
policzony wobec ściany, której nie ma. Liczba jest poprawna dla zbudowanego modelu
i bezużyteczna jako fakt o metrze.

## 2. Uruchomienie

`tools/ci/vehicle_clearance.sh` bierze teraz identyfikator osi jako argument, tak samo
jak `tunnel_alignment.sh` po E1.2:

```bash
bash tools/ci/vehicle_clearance.sh L1_A
bash tools/ci/vehicle_clearance.sh L1_B
bash tools/ci/vehicle_clearance.sh L2_E
```

Workflow liczy skrajnię dla **każdej** osi z macierzy, nie tylko dla pakietu A.

## 3. Błąd: jedna stała wysokość i trzy kopie tego samego progu

### 3.1 Wysokość styku wpisana na stałe

```
BŁĄD: wzór i pomiar na siatce rozjeżdżają się o 148.8 mm — jedna z tych dwóch dróg jest błędna
```

Kontrola krzyżowa („wzór na strzałkę cięciwy wobec pomiaru na siatce") mierzyła
odległość do ściany na **wpisanej na stałe wysokości 1,0 m**. Profil `box_double` ma
ścięte naroża stropu, więc światło zwęża się z wysokością:

| wysokość | światło od osi toru |
|---|---:|
| 1,03 m | **1,250 m** |
| 3,60 m | **1,100 m** |

Minimum pakietu A wypada na 1,03 m, więc stała zgadzała się **przypadkiem**. Minimum
pakietu B wypada na ścięciu naroża, na 3,60 m, i tam stała myli się o 149 mm.
Po zmianie na wysokość, na której naprawdę wypadło minimum, wszystkie sześć
przypadków zgadza się w granicach 3,9 mm.

### 3.2 Symetryczny próg tam, gdzie zjawisko jest kierunkowe

Po naprawie wysokości pakiet E nadal przekraczał próg ±10 mm — o 3,3 mm. Pomiar mówi,
dlaczego:

| pakiet | tor | obiekt | R [m] | przewidziany | zmierzony | zapas |
|---|---:|---|---:|---:|---:|---:|
| A | 0 | articulation_1 | 85,94 | 1,0982 | 1,1000 | +1,8 mm |
| A | 1 | car_2 | 85,94 | 0,9408 | 0,9447 | +3,9 mm |
| B | 0 | articulation_1 | 130,81 | 1,0988 | 1,1000 | +1,2 mm |
| B | 1 | articulation_1 | 130,81 | 1,0988 | 1,1000 | +1,2 mm |
| E | 0 | articulation_1 | 95,56 | 1,0984 | 1,1000 | +1,6 mm |
| E | 1 | car_2 | 95,56 | 0,9720 | 0,9853 | +13,3 mm |

**Wzór jest zachowawczy w 6 z 6 przypadków.** Nie przez przypadek: strzałkę liczy się
z promienia w **środku składu**, a bryła, w której wypada minimum, leży poza środkiem,
gdzie oś jest łagodniejsza — więc wzór przeszacowuje wychylenie i **zaniża** luz.
Symetryczny próg ±10 mm był skalibrowany na samym pakiecie A.

Sprawdziłem oczywistą alternatywę, zanim ruszyłem kontrolę, a nie po: podanie wzorowi
promienia liczonego **na cięciwie samej bryły** pogarsza sprawę — rozjazd pakietu A
rośnie z 3,9 do **69,0 mm**. To nie jest kwestia doboru promienia; rozrzut jest
własnością metody. `clearance_profile.py` mówi to samo od początku, podając trzy
warianty wzoru i etykietując każdy jako optymistyczny albo zachowawczy zamiast
wybierać jeden.

Kontrola sprawdza teraz to, co ta para metod naprawdę ustala:

- wzór **nie może obiecać więcej luzu, niż mierzy siatka** — twarde zero, niezależnie
  od wielkości, bo kontrola skrajni nie ma prawa błądzić w tę stronę;
- wzór nie może być zachowawczy ponad **50 mm** — daleko pod 148,8 mm, którym
  objawiał się błąd stałej wysokości.

### 3.3 Ten sam guard w trzech miejscach

Próg ±10 mm był skopiowany razem z kontrolą i siedział w trzech miejscach:
dwa bloki w `tools/ci/vehicle_clearance.sh` i jeden wewnątrz
`tools/blender/profile_vehicle.py`. Pakiet E wywracał się kolejno na każdym z nich.

Trzeci przypadek jest najbardziej wymowny: `profile_vehicle.py` **sam liczy znak tej
różnicy** i zapisuje go jako `formula_optimistic`, po czym własny guard ten znak
ignoruje i traktuje 12,8 mm zachowawczych tak samo jak 12,8 mm optymistycznych.
Narzędzie znało odpowiedź, a kontrola o nią nie pytała.

`FORMULA_GUARD_MM = 100 mm` w globalnym minimum zostaje bez zmian: tam oś nie jest
łukiem okręgu i ta wartość jest bezpiecznikiem na regresję, nie oceną dokładności.

## 4. Co widać na renderach

**`M7_WORST_gap` pakietu A (0,8999 m) i pakietu E (0,9353 m)** — przekrój poprzeczny
w najgorszym punkcie: obrys tunelu 9,40 × 5,90 m ze ściętymi górnymi narożami,
a wewnątrz obrys składu przesunięty **w prawo**, zgodnie z odsunięciem toru
o +2,10 m. Szczelina do prawej ściany jest wyraźnie węższa niż do lewej i to ona jest
mierzoną liczbą. Oba obrazy wyglądają niemal identycznie — różnica 35 mm na 960 px
kadru to poniżej dwóch pikseli, więc **na oko tych dwóch pakietów nie da się
rozróżnić**; rozróżnia je pomiar, i po to on jest.

**`M7_GAP_flank`** — widok wzdłuż szczeliny między pudłem a ścianą, z siatką drutową.
Widać ciągły pas ściany po jednej stronie i człony składu po drugiej, bez przenikania.

## 5. Kontrole, które przeszły

- **Dwie niezależne implementacje pomiaru** (`place_vehicle` w jednym punkcie
  i `profile_vehicle` przesuwający skład): rozjazd **< 0,5 mm** na każdym pakiecie.
- **Redukcja kandydatów** (1306 z 5384 wierzchołków na pakiecie A): rozjazd wobec
  pełnego przebiegu **0,0000 mm** na wszystkich sprawdzanych pozycjach.
- **Negatyw**: próg 5 m luzu wywraca przebieg w każdym pakiecie.
- **Determinizm**: dwa przebiegi tego samego kodu dają identyczny raport.
- **Zamiatana obwiednia** zawiera wszystkie wierzchołki pojazdu w każdej pozycji.

```
$ bash tools/ci/vehicle_clearance.sh L1_A   ->  exit=0
$ bash tools/ci/vehicle_clearance.sh L1_B   ->  exit=0
$ bash tools/ci/vehicle_clearance.sh L2_E   ->  exit=0

$ python3 tools/tests/test_all.py
  367/367 przeszło
```

## 6. Czego świadomie nie zrobiono

- **Nie policzono profilu dla C, D ani F** — nie mają tuneli (E1.2 §1).
- **Nie zmieniono profilu `box_double`.** Wymiary są `design_assumption`
  (`docs/21-measured-vs-assumed.md`) i należą do R-005 (#17). Gdyby prawdziwe światło
  tunelu STIB było węższe niż 9,40 m, wszystkie liczby z §1 trzeba przeliczyć.
- **Nie modelowano wychylenia zewnętrznego końców składu** — `m7-spec.json` nie ma
  rozstawu czopów skrętu. Nie ma też przechyłki, ugięcia zawieszenia, zużycia kół,
  tolerancji toru ani rozjazdów. Każdy z tych czynników zjada część zmierzonego luzu.
- **Nie postawiono progu dopuszczalnego luzu.** 0,8999 m to pomiar, nie ocena; czy to
  dużo, czy mało, zależy od normy, której nie ma w `data/` ani w `docs/`.
