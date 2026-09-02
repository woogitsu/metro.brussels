# T-211 (1/2) — perony liczone z osi i ze skrajni

Stan: **2026-09-02**. Wyjście: `tools/track/station_layout.py`,
`tools/tests/test_station_layout.py`. Odblokowane przez
[`reports/R-007-platform-dimensions.md`](R-007-platform-dimensions.md).

Ten sam podział, co w T-011: **tu liczą się kilometraże i granice**, bryły buduje
osobne narzędzie w Blenderze (etap 2). Pierwsza połowa nie ma ani jednej decyzji
projektowej i testuje się bez Blendera.

---

## 1. Znalezisko: `platform_edge_x` z profilu to nie jest krawędź peronu

Profil `station` w `tools/blender/profiles.py` ma pole nazwane `platform_edge_x`
o wartości `[-4.05, 4.05]`, przy torach na `±2,10 m`. Gdyby postawić tam peron,
szczelina do pudła M7 wyszłaby:

```
odsunięcie krawędzi od toru       1,95 m
pół szerokości M7                −1,35 m
                                 ───────
szczelina peron–pudło             0,60 m
```

**Sześćdziesiąt centymetrów.** To nie jest szczelina, tylko przepaść, do której
wpada noga. Arytmetyka wyjaśnia, skąd ta liczba:

```
1,95 = 1,35 (pół szerokości M7) + 2 × 0,30 (CLEARANCE_M)
```

Czyli `platform_edge_x` opisuje **granicę skrajni**, a nie krawędź peronu — nazwa
pola myli. Nic w repo tego pola nie czytało (sprawdzone gremem po `tools/` i `src/`),
więc nikt się na tym nie przejechał, ale pierwsze narzędzie, które by je wzięło za
krawędź, postawiłoby peron 60 cm od pociągu.

`station_layout.py` **nie bierze tej wartości**. Liczy własną dolną granicę.

## 2. Skąd bierze się dolna granica odsunięcia

Sztywne pudło członu opiera się na łuku **cięciwą**, więc jego środek wchodzi do
wnętrza łuku o strzałkę. Peron postawiony bliżej niż `pół szerokości + strzałka`
byłby w kolizji. To jest granica **policzona z geometrii**, nie założenie:

```
minimalne odsunięcie = M7_WIDTH_M / 2 + versine(cięciwa członu, promień lokalny)
```

Cięciwa członu: 94,0 m / 6 = **15,667 m** (długość i liczba członów ze specyfikacji;
równy podział to `DESIGN_EQUAL_CAR_SPLIT`). Zmierzone na pakiecie A:

| stacja | od | do | dł. | R | strzałka | min. odsunięcie |
|---|---:|---:|---:|---:|---:|---:|
| Gare de l'Ouest | 0,0 | 47,0 | **47,0** ✂ | 1397 | 0,0220 | 1,3720 |
| Beekkant | 462,7 | 556,7 | 94,0 | 114922 | 0,0003 | 1,3503 |
| Étangs Noirs | 1404,9 | 1498,9 | 94,0 | 365 | 0,0840 | 1,4340 |
| Comte de Flandre | 2007,8 | 2101,8 | 94,0 | 343 | 0,0896 | 1,4396 |
| Sainte-Catherine | 2673,8 | 2767,8 | 94,0 | 165 | 0,1863 | 1,5363 |
| De Brouckère | 3082,9 | 3176,9 | 94,0 | 228 | 0,1346 | 1,4846 |
| **Gare Centrale** | 3684,8 | 3778,8 | 94,0 | **137** | **0,2248** | **1,5748** |
| Parc | 4028,7 | 4122,7 | 94,0 | 6015 | 0,0051 | 1,3551 |
| Arts-Loi | 4513,9 | 4607,9 | 94,0 | 26300 | 0,0012 | 1,3512 |
| Maelbeek | 5105,4 | 5199,4 | 94,0 | 82030 | 0,0004 | 1,3504 |
| Schuman | 5420,4 | 5514,4 | 94,0 | 630 | 0,0487 | 1,3987 |
| Merode | 6639,4 | 6686,7 | **47,4** ✂ | 915 | 0,0335 | 1,3835 |

Najciaśniej jest w **Gare Centrale**: promień 137 m daje strzałkę 22,5 cm, więc
krawędź musi odsunąć się o 1,5748 m zamiast 1,35 m. Różnica między najprostszym
a najciaśniejszym peronem to **22,4 cm** — dość, żeby peron zaprojektowany na
prostej wchodził w kolizję na łuku.

Granica z profilu (1,95 m) jest **wyższa od najgorszego przypadku**, więc profil nie
jest za ciasny — jest za luźny o co najmniej 0,375 m.

## 3. Czego to narzędzie nie wymyśla

**Szczeliny peron–pudło.** R-007 ustalił, że nie podaje jej żadne publiczne źródło.
`--platform-gap-m` **nie ma wartości domyślnej**: bez niej `edge_offset_m` wychodzi
`None`, a nie liczba.

```
[PERONY] szczelina peron–pudło NIE PODANA — edge_offset_m zostaje null,
         bo zero znaczyłoby „peron dotyka pudła"
```

Ten sam wzorzec, co `braking_distance_m` w T-011 i `--brake-from-kmh` bez wartości
domyślnej: **zero to nie jest „nie wiem"**.

**Wychylenia zewnętrznego końców składu.** Wymaga rozstawu czopów skrętu, którego nie
ma w `m7-spec.json` — T-220 celowo nie wymyślił wózków. To samo zastrzeżenie, co
w `clearance.py`: wynik jest **warunkiem koniecznym**, nie pełną skrajnią kinematyczną.

## 4. Wysokość peronu to jedna liczba, nie dwie

R-007: STIB pisze, że podłoga M7 (1 m 03) jest *„à hauteur du quai"*.
`station_layout.py` czyta więc `floor_height_m` **z rejestru**, zamiast trzymać własną
kopię — test pilnuje tej tożsamości.

Uwaga na profil: `station` ma `platform_height_m: 1.05`, a **1,05 m to wysokość podłogi
M6**, nie M7 (dosłownie z karty STIB: *„1m03 contre 1m05 pour les M6"*). Symulator
jeździ M7 po liniach 1 i 5. Profilu w tym PR nie zmieniam — to geometria tunelu, więc
zmiana idzie z etapem 2, razem z renderem kontrolnym. Test przypina rozjazd, żeby nie
zniknął po cichu.

## 5. Długość peronu

Domyślna wartość to **94,0 m = długość składu M7** (`spec`, źródło STIB) — dolna granica
z R-007, a nie 94,76 m z pomiaru obrysów OSM. Peron krótszy od składu jest odrzucany:

```
peron 93.90 m jest krótszy od składu M7 (94.00 m); R-007 wyprowadza z tego dolną
granicę, bo STIB nie stosuje selektywnego otwierania drzwi
```

Górna granica z obrysu stacji (`--footprint-m`) jest **kontrolą**, nie wymiarem: peron
dłuższy niż bryła stacji jest na pewno błędny. Najciaśniejszy przypadek pakietu A to
Parc, 109,1 m.

## 6. Przycięcie do końców osi

Dwa perony są przycięte i **narzędzie to mówi**, zamiast raportować pełne 94 m:
Gare de l'Ouest (47,0 m — stacja leży na kilometrażu 0,0) i Merode (47,4 m — na samym
końcu osi, 6686,35 m przy długości 6686,74 m).

To nie jest błąd danych, tylko granica pakietu: oba perony wychodzą poza odcinek, który
pakiet A modeluje. Zapisane tak samo jak `CbtcTestSpan` w T-314 — flaga, nie milczenie.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py  ->  635/635 przeszło   (przed T-211: 623)
```

Osiem kontroli negatywnych, każda wpisana i cofnięta:

| mutacja | wynik |
|---|---|
| wysokość peronu wpisana na sztywno 1,05 | 632/635 |
| szczelina dostaje domyślne zero | 634/635 |
| brak bramki na peron krótszy od składu | 634/635 |
| przycięcie zawsze `False` | 634/635 |
| strzałka łuku pomijana | 634/635 |
| peron nie jest wyśrodkowany na stacji | 632/635 |
| kontrola obrysu zawsze `True` | 634/635 |
| znika zastrzeżenie o czopach skrętu | 634/635 |

## 8. Co zostaje na etap 2

Bryły: płyta peronu, krawędź, komora stacyjna — w Blenderze, z renderem kontrolnym
i obejrzeniem trzech PNG. Wtedy też decyzja o `platform_height_m` w profilu `station`
(1,05 → 1,03) i o nazwie pola `platform_edge_x`, bo obie zmieniają geometrię tunelu
i muszą przejść przez `tunnel-alignment.yml`.
