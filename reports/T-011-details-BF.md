# Znaczniki kilometrażu i detale na pakietach B–F (T-011, ciąg dalszy)

**Zmierzone 06.09.2026 na commicie:** `154ad30`

`reports/T-011-detail-markers.md` podał rozbicie dla pakietu A i zostawił pięć
pozostałych osi. Ten raport je domyka: te same narzędzie i te same dwa parametry,
inne wejście.

Narzędzie: `tools/track/detail_layout.py`, bez ani jednej zmiany w kodzie.

## 1. Sześć osi, jedno polecenie

```bash
for AXIS in L1_A L1_B L5_C L5_D L2_E L6_F; do
    python3 tools/track/detail_layout.py --axis "data/track/$AXIS.json" \
        --out "build/details/$AXIS.json" --brake-from-kmh 72
done
```

| pakiet | oś | długość [m] | hektometry | stacje | punkty hamowania | razem |
|---|---|---:|---:|---:|---:|---:|
| A | `L1_A` | 6686,4 | 66 | 12 | 11 | **89** |
| B | `L1_B` | 5083,2 | 50 | 9 | 8 | **67** |
| C | `L5_C` | 5386,4 | 53 | 9 | 8 | **70** |
| D | `L5_D` | 3847,2 | 38 | 7 | 6 | **51** |
| E | `L2_E` | 9020,8 | 90 | 17 | 16 | **123** |
| F | `L6_F` | 4456,7 | 44 | 7 | 6 | **57** |
| **razem** | | **34 480,6** | **341** | **61** | **55** | **457** |

Wiersz pakietu A zgadza się co do sztuki z kryterium pozycji 6.B2 — **89 miejsc =
66 hektometrów + 12 stacji + 11 punktów hamowania** — więc pozostałe pięć wierszy
policzono tą samą drogą, a nie inną.

## 2. Trzy zależności, które ta tabela musi spełniać, i spełnia

**Hektometry = `floor(długość / krok)`.** Sprawdzone dla każdej z sześciu osi
osobno: 66, 50, 53, 38, 90, 44 wobec 66,86 / 50,83 / 53,86 / 38,47 / 90,21 / 44,57.
Znacznik na kilometrażu 0 jest stacją, nie hektometrem — dlatego liczba jest podłogą,
a nie podłogą plus jeden.

**Punkty hamowania = stacje − 1.** Pierwsza stacja osi nie dostaje punktu hamowania,
bo nie ma przed nią odcinka. Zachodzi we wszystkich sześciu pakietach: 11/12, 8/9,
8/9, 6/7, 16/17, 6/7. Pole `skipped_brake_points` jest **puste dla każdej osi** —
żaden punkt nie wypadł przed poprzednią stacją, co przy najkrótszych odcinkach
pakietu D nie było oczywiste.

**Każda stacja ma `stop_id`.** 61 z 61, zero braków. Identyfikatory pochodzą
z `data/track/*.json`, czyli z geometrii STIB (T-111), a nie z dopasowania po nazwie.

## 3. Dlaczego 61 stacji, skoro sieć ma 59

Osie pakietów zachodzą na siebie na stacjach krańcowych: oś zaczyna się i kończy
**w środku** peronu stacji krańcowej, więc ta sama stacja bywa policzona w dwóch
pakietach. To samo zjawisko opisuje `reports/T-211-stations-BF.md` przy peronach
(„każda oś ma dokładnie dwa perony przycięte"). Liczba 61 jest więc sumą po osiach,
nie liczbą stacji sieci — i tak ma być, bo znaczniki są zasobem **osi**, nie sieci.

## 4. Punkty hamowania są parametrem scenariusza, nie danymi o torze

Prędkość 72 km/h nie jest prędkością dopuszczalną na torze. **Nie ma jej źródła**
(R-006), więc wolno jej użyć wyłącznie jako **zadeklarowanego parametru przebiegu** —
i tak jest tu użyta, jawnie w wierszu polecenia.

Bez `--brake-from-kmh` narzędzie nie stawia ani jednego punktu hamowania i podaje
`braking_distance_m: None`, a nie `0.0`. Zmierzone na tych samych sześciu osiach:
89 → 78, 67 → 59, 70 → 62, 51 → 45, 123 → 107, 57 → 51 miejsc. Różnica to dokładnie
liczba punktów hamowania z tabeli wyżej.

Rozróżnienie „brak danych" od „zero" jest tu całą treścią: `0.0` znaczyłoby, że
pociąg hamuje na długości zerowej, a `None` — że nikt nie zadeklarował, z jakiej
prędkości.

## 5. Bramka

`tools/tests/test_detail_layout.py` dostaje pięć testów, które liczą te same
wielkości **z osi** i porównują z tabelą §1 **odczytaną z tego pliku**. Raport jest
stroną porównywaną, tak samo jak w `test_readme_claims.py`: w teście nie stoi ani
jedna liczba z tej tabeli.

Osiem wcześniejszych testów tego modułu bada zachowanie narzędzia na figurach
liczonych w locie; te pięć bada, że narzędzie **wypuszczone na prawdziwe osie** daje
to, co raport twierdzi.

## 6. Czego ten raport nie zrobił

- **Nie ruszył brył znaczników.** `tools/blender/detail_markers.py` wymaga Blendera
  i pętli weryfikacji z `CLAUDE.md` §5 — bez niego kończy się na kilometrażach.
  Blendera w tym środowisku nie ma, więc etap geometrii zostaje otwarty.
- **Nie zmienił ani jednej linii w `tools/track/detail_layout.py`.** Pozycja była
  „to samo narzędzie, inne wejście" i taka została.
- **Nie dopisał wartości domyślnej dla `--brake-from-kmh`.** Jej brak jest decyzją
  z T-011 i sekcja 4 mówi dlaczego.

## 7. Weryfikacja — rzeczywiste wyjście

```
[DETALE] L1_A: 6686.4 m osi, 89 miejsc — brake 11, hectometre 66, station 12
[DETALE] L1_B: 5083.2 m osi, 67 miejsc — brake 8, hectometre 50, station 9
[DETALE] L5_C: 5386.4 m osi, 70 miejsc — brake 8, hectometre 53, station 9
[DETALE] L5_D: 3847.2 m osi, 51 miejsc — brake 6, hectometre 38, station 7
[DETALE] L2_E: 9020.8 m osi, 123 miejsc — brake 16, hectometre 90, station 17
[DETALE] L6_F: 4456.7 m osi, 57 miejsc — brake 6, hectometre 44, station 7
```
