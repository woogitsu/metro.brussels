# M7 w tunelu pakietu A — skrajnia zmierzona na siatce

Pierwsza scena, w której pojazd i infrastruktura istnieją razem. Do tej pory
`reports/M7-curve-clearance.md` liczył luz **ze wzoru** na strzałkę cięciwy; tutaj
ten sam luz jest mierzony **na siatce**: każdy wierzchołek pojazdu dostaje offsety
względem lokalnej ramki osi i odległość do obrysu profilu.

Dwie niezależne drogi do jednej liczby. Jeżeli się rozjadą, jedna z nich jest błędna
i trzeba to zobaczyć, a nie uśrednić.

- narzędzia: `tools/blender/place_vehicle.py` (bpy) + `tools/blender/placement.py` (matematyka, czysty Python)
- testy: `tools/tests/test_placement.py`
- odtworzenie: `bash tools/ci/vehicle_clearance.sh` (~20 s)
- w CI: job `tunnel-alignment`

## 1. Jak osadzony jest skład

Skład M7 jest **przegubowy**: sześć sztywnych pudeł i pięć mieszków. Na łuku każde
pudło opiera się na **własnej cięciwie**, więc ustawienie całych 94 m jako jednej
bryły dałoby geometrię, której na torze nie ma. Każda bryła dostaje więc osobną
transformację, wyznaczoną z cięciwy łączącej jej dwa końce na osi.

Poziom odniesienia nie wprowadza ani jednego nowego założenia: układ pojazdu
z `m7_shell.py` ma główkę szyny na Z = 0, a profile w `profiles.py` mają ten sam
poziom odniesienia — `vehicle_gauge` zaczyna się na y = −0,10 względem główki szyny
i `fits_gauge` porównuje to bezpośrednio z obrysem profilu.

Rzeczywiste bryły w GLB (nie nominalny podział 94/6):

| bryła | długość |
|---|---|
| `M7_car_1`, `M7_car_6` (skrajne, z kabiną) | 15,117 m |
| `M7_car_2`…`M7_car_5` (środkowe) | 14,567 m |
| `M7_articulation_1`…`_5` | 1,100 m |

## 2. Wynik — oba tory na najciaśniejszym łuku

Najgorszy punkt osi wybierany automatycznie: chainage **2518,8 m**, promień na cięciwie
pudła **85,94 m** (między Comte de Flandre a Sainte-Catherine).

| tor | offset | zmierzony minimalny luz | gdzie |
|---|---|---|---|
| 0 | −2,10 m | **+1,1000 m** | `M7_articulation_1`, strop, wysokość 3,600 m |
| 1 | +2,10 m | **+0,9447 m** | `M7_car_2`, ściana, bok +3,755 m, wysokość 1,030 m |

Luz per bryła na torze 1: `car_1` +0,9675 · `car_2` +0,9447 · `car_3` +0,9526 ·
`car_4` +0,9530 · `car_5` +0,9830 · `car_6` +1,0673 · wszystkie przeguby +1,1000.

Dwie rzeczy warte odczytania z tej tabeli:

- **Na torze 0 wiąże strop, nie ściana.** Na tym łuku pudło przesuwa się ku środkowi
  otworu, więc krytyczna staje się wysokość: 4,70 m stropu minus 3,60 m dachu = 1,10 m.
  Ta wartość **nie zależy od promienia**, bo pojazd nie zmienia wysokości — stąd
  identyczny wynik dla wszystkich pięciu przegubów.
- **Przeguby nigdy nie są krytyczne w poziomie.** Są węższe (±1,17 m wobec ±1,35 m)
  i krótsze, więc ich strzałka jest pomijalna.

## 3. Kontrola krzyżowa: wzór wobec siatki

```
[KONTROLA] promień 85.94 m, cięciwa nominalna 15.667 m, rzeczywista 14.567 m -> strzałka 309.2 mm
[KONTROLA] luz statyczny do ściany 1.2500 m, przewidziany 0.9408 m, zmierzony 0.9447 m
[KONTROLA] rozjazd wzoru i siatki: 3.9 mm
```

**Zgodność 3,9 mm.** Reszta to różnica między prostokątnym narożnikiem pudła a punktem
w połowie cięciwy, czyli dokładnie to, czego wzór nie modeluje.

Przy pierwszej próbie rozjazd wynosił **52,4 mm** — bo kontrola brała cięciwę nominalną
15,667 m (94/6) zamiast rzeczywistych 14,567 m pudła, w którym wypadło minimum. To nie
był błąd geometrii, tylko porównywanie dwóch różnych wielkości. Model analityczny
z `reports/M7-curve-clearance.md` jest przez to **zachowawczy o ok. 50 mm**, co jest
własnością pożądaną, ale trzeba o niej wiedzieć.

Warto też odnotować różnicę wielkości: `profiles.min_clearance` (1,078 m) to maksymalna
**symetryczna** inflacja skrajni i bywa wiązana przez ścięcie naroża stropu, natomiast
luz do ściany na torze ±2,10 m wynosi 1,250 m. To dwie różne liczby i raport skrajni
używa tej pierwszej, bardziej zachowawczej.

## 4. Obejrzane rendery

Nowy zestaw kamer `clearance` (`manifest_version` 2026-09-01.4).

- **`gap`** — przekrój o głębi **3 m** w punkcie zmierzonego minimum. Obrys `box_double`
  z oboma ścięciami naroży stropu, a w nim pudło M7 wyraźnie przesunięte w prawo.
  Przy kadrze 12 m na 960 px (80 px/m) szczelina do prawej ściany ma **78 px ≈ 0,98 m**
  wobec zmierzonych 0,945 m, a nad dachem **90 px ≈ 1,13 m** wobec 1,10 m. **Luz da się
  odczytać z obrazu i zgadza się z liczbą.** Przy głębi 30 m (jak w zestawie `alignment`)
  obrys pojazdu rozmazuje się po łuku i nie da się z niego nic odczytać — stąd osobny zestaw.
- **`approach`** — widok z toru na nadjeżdżający skład: czoło M7 wyłania się zza łuku,
  widoczne otwory drzwiowe na boku, proporcje pojazdu wobec otworu tunelu poprawne,
  ściany i strop widziane od wewnątrz.
- **`flank`** — elewacja odcinka 30 m z płaszczyzną bliską tnącą w osi. Widać regularny
  rząd otworów drzwiowych M7 na tle grubej triangulacji tunelu.

**Bez overlaya siatki `flank` pokazywał jednolity szary pas.** Materiał kontrolny jest
z założenia jeden dla całej sceny, więc w scenie złożonej nic nie odróżnia pudła od
ściany. Dlatego kamery `gap` i `flank` deklarują `wire: true` **w manifeście** — to
wiedza o kamerze, nie o wywołaniu. Bez cięcia płaszczyzną w osi `flank` pokazywał samą
ścianę: tunel jest zamkniętą rurą i zasłania własne wnętrze.

## 5. Czego ten pomiar NIE obejmuje

- **zwisu czopów skrętu** — brak rozstawu w `data/vehicle/m7-spec.json`; T-220 świadomie
  nie wymyślił wózków. Zwis końcowy działa w przeciwną stronę niż strzałka, więc
  **rzeczywisty luz jest mniejszy niż tu zmierzony**;
- przechyłki, ugięcia zawieszenia, zużycia kół, tolerancji toru i budowlanej tunelu;
- profilu pionowego — T-112 (#10) zablokowane, cała scena leży na Z = 0;
- niepewności samego promienia: 85,94 m to wariant „optymistyczny" z
  `reports/M7-curve-clearance.md`; na łamanej źródłowej wychodzi 50,87 m i wtedy luz
  spada odpowiednio;
- niepewności szerokości otworu: `box_double` ma 9,40 m jako wymiar **projektowy**,
  a pomiar z UrbIS daje 8,25–9,92 m (`reports/M7-curve-clearance.md`, sekcja 4);
- **niepewności rozstawu torów**: cały pomiar zakłada `track_offsets` ±2,10 m
  z `profiles.py`, czyli wartość bez źródła. Pomiar z INSPIRE Rails
  (`reports/L1_A-track-spacing.md`) daje ±1,647 m, czyli tory **bliżej siebie
  o 0,91 m**. Gdyby to potwierdzić, pudło stałoby dalej od ściany i luz by wzrósł —
  ale jednocześnie zmierzony otwór jest węższy od projektowego, więc obu poprawek
  nie wolno liczyć osobno.

## 6. Co z tego wynika

Luz zostaje dodatni na obu torach i w obu metodach, ale **cztery niezależne niepewności
działają w tę samą stronę** — mniejszy promień, węższy otwór, zwis czopów, przechyłka.
Piąta, rozstaw torów, działa w przeciwną. Żadnej z nich nie wolno domykać zgadywaniem.
Zanim ktokolwiek uzna 0,94 m za zapas, musi zostać domknięte R-005 (#17): przekrój
tunelu i geometria toru ze źródła, a nie z projektu.
