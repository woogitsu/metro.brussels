# Perony pakietów B–F — ta sama poprzeczka co pakiet A (6.B1)

**Zmierzone 05.09.2026 na commicie:** `527f509`

Pozycja 6.B1 z kolejki: `tools/track/station_layout.py` liczył dotąd wyłącznie pakiet A.
Ten raport stosuje to samo narzędzie do pięciu pozostałych osi i opisuje **wyłącznie
różnice, rozstrzygnięcia i zmierzone liczby**. Metoda, uzasadnienie dolnej granicy
odsunięcia krawędzi i to, czego narzędzie świadomie nie liczy, są w
`reports/T-211-station-layout.md` i nie powtarzam ich tutaj.

Wariant jak wszędzie: `--platform-length-m design`, czyli 95,0 m z decyzji właściciela
(T-212, `station_components.DESIGN_PLATFORM_LENGTH_M`). Bez tego słowa narzędzie bierze
dolną granicę 94,0 m i buduje perony o metr za krótkie — to jest ta sama pułapka, którą
opisuje `station_layout.py` w nagłówku.

## 0. Kontrola metody: pakiet A wychodzi tak samo jak w T-211

Zanim liczby z pięciu nowych osi cokolwiek znaczą, ten sam przebieg musi odtworzyć
pakiet A. Odtwarza, co do czwartego miejsca po przecinku:

| wielkość | `reports/T-211-station-layout.md` | ten przebieg |
|---|---|---|
| peronów | 12 | 12 |
| najciaśniejszy | Gare Centrale, R = 137 m | Gare Centrale\|Centraal Station, R = 136,60 m |
| strzałka cięciwy tam | 22,5 cm | 0,2248 m |
| odsunięcie krawędzi tam | 1,5748 m | 1,5748 m |
| rozpiętość w pakiecie | 22,4 cm | 0,2245 m |

## 1. Sześć pakietów, 61 peronów

| pakiet | oś | długość osi [m] | peronów | przyciętych | najciaśniejszy peron | R_min [m] | strzałka [m] | odsunięcie min. [m] | rozpiętość [m] |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| A | `L1_A` | 6686,7 | 12 | 2 | Gare Centrale\|Centraal Station | 136,60 | 0,2248 | 1,5748 | 0,2245 |
| B | `L1_B` | 5083,5 | 9 | 2 | Montgomery | 119,54 | 0,2569 | 1,6069 | 0,2567 |
| C | `L5_C` | 5386,7 | 9 | 2 | Veeweyde\|Veeweide | 161,61 | 0,1900 | 1,5400 | 0,1881 |
| D | `L5_D` | 3847,3 | 7 | 2 | Demey | 721,25 | 0,0425 | 1,3925 | 0,0423 |
| E | `L2_E` | 9021,1 | 17 | 2 | Trône\|Troon | 97,11 | 0,3164 | 1,6664 | 0,3163 |
| F | `L6_F` | 4456,9 | 7 | 2 | Houba-Brugmann | 331,92 | 0,0924 | 1,4424 | 0,0921 |

Pakiety B–F dają **49 peronów**, razem z pakietem A jest ich **61**. Liczba peronów
w każdym pakiecie zgadza się z liczbą wpisów `stations` w pliku osi — narzędzie nie
gubi ani nie dokłada stacji, i pilnuje tego test.

## 2. Najciaśniejszy peron sieci nie jest w pakiecie A

**Trône\|Troon na osi `L2_E`, R = 97,11 m.** Strzałka cięciwy członu wychodzi tam
0,3164 m, więc krawędź peronu musi odsunąć się o **1,6664 m** zamiast 1,35 m — o
**9,2 cm dalej** niż najgorszy peron pakietu A i o **31,6 cm** dalej niż na prostej.

Trzy pakiety mają peron ciaśniejszy niż średnia pakietu A (B, C i E), a dwa są wyraźnie
prostsze: **D jest najprostszy w całej sieci** — Demey R = 721,25 m daje strzałkę
4,25 cm, czyli praktycznie prostą.

Znaczenie tej rozpiętości jest to samo, co w T-211 i warto je powtórzyć w liczbach
z sześciu pakietów, a nie jednego: peron zaprojektowany na prostej i postawiony na
najciaśniejszym łuku sieci byłby o **31,6 cm** za blisko osi. Rozpiętość wewnątrz
jednego pakietu sięga **31,63 cm** (E) i schodzi do **4,23 cm** (D).

## 3. Perony krańcowe są przycięte na wszystkich sześciu osiach — i to nie jest usterka

Każda oś ma **dokładnie dwa** perony przycięte, po jednym na każdym krańcu:

| oś | przycięty na starcie | przycięty na końcu |
|---|---|---|
| `L1_A` | Gare de l'Ouest\|Weststation — 47,5 m | Merode — 47,9 m |
| `L1_B` | Montgomery — 47,5 m | Stockel\|Stokkel — 47,7 m |
| `L2_E` | Elisabeth — 47,5 m | Beekkant — 47,8 m |
| `L5_C` | Jacques Brel — 47,5 m | Erasme\|Erasmus — 47,8 m |
| `L5_D` | Thieffry — 47,5 m | Herrmann-Debroux — 47,6 m |
| `L6_F` | Belgica — 47,5 m | Roi Baudouin\|Koning Boudewijn — 47,7 m |

Powód jest wspólny i wynika z tego, jak wycięto osie w T-111: **oś zaczyna się
i kończy w środku stacji krańcowej**. Peron jest wyśrodkowany na kilometrażu stacji,
więc na starcie zostaje z niego dokładnie połowa (47,5 m z 95,0 m), a na końcu tyle,
ile zostało osi po ostatnim kilometrażu.

Konsekwencja jest praktyczna, nie kosmetyczna: **połowa peronu każdej stacji krańcowej
leży poza modelowaną osią**. Kto zbuduje z tego geometrię, dostanie na obu krańcach
peron o połowie długości — i nie jest to błąd narzędzia, tylko zakres danych.
`clipped_at_start` / `clipped_at_end` są w wyjściu właśnie po to, żeby to było widać,
a nie żeby milczeć.

## 4. Czego ten przebieg nie rozstrzyga

- **`edge_offset_m` jest `None` we wszystkich 61 wierszach**, bo `--platform-gap-m` nie
  ma wartości domyślnej i mieć jej nie może: R-007 ustalił, że szczeliny peron–pudło nie
  podaje żadne publiczne źródło. To, co ten raport podaje, to `minimum_edge_offset_m` —
  **dolna granica z geometrii**, a nie wymiar peronu.
- **Wysokość peronu** jest jedna dla wszystkich pakietów (1,03 m, status `spec`)
  i pochodzi z rejestru M7, nie z pomiaru na tych osiach.
- **Bryły w Blenderze** to etap 2 T-211 i osobna pozycja; ten przebieg kończy się na
  kilometrażach i granicach, czyli na tym, co da się sprawdzić bez Blendera.
- **Profil pionowy** — wszystkie sześć osi ma `vertical.status = "not_modelled"`
  (T-112 zablokowane), więc promienie tutaj są promieniami w rzucie poziomym.

## 5. Weryfikacja — rzeczywiste wyjście

```
$ for AXIS in L1_A L1_B L2_E L5_C L5_D L6_F; do \
      python3 tools/track/station_layout.py --axis "data/track/$AXIS.json" \
          --out "build/stations/$AXIS.json" --platform-length-m design; done
L1_A ok
L1_B ok
L2_E ok
L5_C ok
L5_D ok
L6_F ok

$ python3 tools/tests/test_all.py
  1590/1590 przeszło
```

Niezmiennik `minimum_edge_offset_m = 1,35 + strzałka` sprawdzony na wszystkich
**61 peronach sześciu pakietów**: zero wierszy go łamiących.

Co dokładnie pilnuje bramka, żeby to zdanie nie obiecywało więcej, niż robi:

- **tabela §1** jest PARSOWANA z tego pliku przez `tools/tests/test_station_layout.py`
  i porównywana z przebiegiem liczba w liczbę, bez tolerancji
  (`test_the_BF_report_numbers_are_reproducible_from_the_axes`). Kontrola negatywna
  wykonana na tym pliku: podmiana `1,6664` → `1,6665` w wierszu pakietu E daje
  `['L2_E.offset_m: przebieg 1.6664, raport 1.6665']`;
- **twierdzenie z §3** — dokładnie dwa przycięte perony na oś, pierwszy i ostatni,
  przycięty na starcie ma połowę długości — jest sprawdzane STRUKTURALNIE na sześciu
  osiach (`test_every_axis_clips_exactly_its_two_terminus_platforms`), a nie przez
  parsowanie tamtej tabeli. Nazwy stacji w §3 są więc wypisem z przebiegu, nie
  wejściem bramki.
