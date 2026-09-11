# 6.D140 — okno kadru zawęża wszystkie cztery kamery, a wpis twierdził, że jedną

**11.09.2026**, na `4358ab5`, Blender 5.2.1. Pozycja mówiła, że `--from-m/--to-m`
zawęża **wyłącznie** kamerę klatki `_inside`, a `_iso` i `_side` nadal kadrują cały
obiekt — i że dla osi 78 : 1 `_side` jest kreską **niezależnie od okna**.

## 1. Premisa wpisu jest nieprawdziwa i obalił ją pomiar

Oś `L1_A`, `box_double`: 5452,5 m długości, 5,9 m wysokości, **924 : 1**.

| | `cam_iso` | `cam_side` |
|---|---|---|
| bez okna | distance **7920,3 m**, ink 0,00277 | distance **7677,3 m**, ink 0,00292 |
| okno 400–500 m | distance **137,3 m**, ink **0,11039** | distance **133,1 m**, ink **0,10808** |

Czterdziestokrotna różnica w pokryciu klatki. Powód jest w kodzie i widać go dopiero
po przeczytaniu kolejności: `render_check.main` podstawia `center` i `size` **z okna**,
zanim zbuduje pierwszą kamerę — więc okno rządzi wszystkimi czterema.

## 2. Cztery klatki z oknem 400–500 m — obejrzane

* **`_iso`** — ukośna jasna wstęga tunelu na ciemnym tle, biegnąca z lewego dolnego rogu
  ku prawej krawędzi; widać grubość pudła i załamanie na górnej krawędzi. Nie jest to
  ani pusta scena, ani punkt. Ocenialne.
* **`_side`** — ta sama bryła z boku: przy lewej krawędzi szeroka na kilkadziesiąt
  pikseli, zwęża się ku prawej do włosa i tam załamuje w poziom. Widać przebieg pionowy
  (spadek i wypłaszczenie) — czyli dokładnie to, co §5 przypisuje tej klatce.
* **`_normals`** — **jednolite ciemnoszare pole, bez jednej krawędzi.** Siedem poziomów
  szarości w zakresie 0,3373–0,3451, odchylenie 0,00172. `tylna_strona=0,00000`, czyli
  cała klatka to PRZODY ścian. Jest to wynik **poprawny** i klatka wygląda tak
  z założenia (docstring `make_normals_material`), ale gołym okiem jest nieodróżnialna
  od pustej sceny — patrz §4.
* **`_inside`** — wnętrze tunelu z nakładką siatki: prostokątne pierścienie zbiegające
  się do punktu, ciemne krawędzie na jasnym tle, przekrój czytelny na całej głębi.
  Najbogatsza z czterech (548 poziomów szarości). Ocenialne bez zastrzeżeń.

Dla porównania, **bez** okna: `_iso` jest cienką łamaną linią rysującą rzut osi na
płaszczyznę — widać przebieg trasy, nie widać tunelu; `_side` jest pojedynczym włosem
przez środek kadru. Obie przechodzą podłogę pustej klatki.

## 3. Jak czytelność zależy od okna — zmierzone

| okno | proporcje | `ink` w `_side` |
|---|---:|---:|
| 100 m | 17 : 1 | 0,10808 |
| 300 m | 51 : 1 | 0,04044 |
| 1000 m | 169 : 1 | 0,01278 |
| 3000 m | 508 : 1 | 0,00556 |
| bez okna | 924 : 1 | 0,00292 |

Spadek jest gładki, a **podłoga pustej klatki (`ink` 0,0002) nie zapala się w żadnym
z pięciu przypadków** — także przy 924 : 1, gdzie obejrzana klatka jest włosem. To nie
jest wada podłogi: kod mówi o niej wprost „PODŁOGA, nie miara czytelności".

Liczbą, która przewiduje kształt `_side`, nie jest długość osi, tylko **proporcje okna**.
Stąd poprawka w wypisie, a nie w zachowaniu.

## 4. Rozstrzygnięcie

**Zachowania nie zmieniam — zmieniam to, co widać w logu.** Okno ma zawężać wszystkie
cztery kamery i zawęża; `_iso` ma pokazywać pustą scenę i geometrię zwiniętą w punkt
i pokazuje. Brakowało czegoś innego: **nigdzie nie było widać, których klatek okno
dotyczy** — i właśnie z tego wziął się wpis tej pozycji.

Wypis mówi dziś:

```
[OKNO] os 400.0-500.0 m (dlugosc 100.0 m) center=(123.6,431.8,0.0) size_m=94.5
[OKNO] zaweza kamery: cam_iso, cam_side, cam_normals, cam_inside
[OKNO] proporcje okna 17 : 1 (dlugosc 100.0 m / wysokosc 5.9 m) — im wieksze, tym
       bardziej `_side` jest kreska; progu tu nie ma, patrz camera_aim.proporcje_okna
```

**Progu nie stawiam i to jest wybór, nie przeoczenie.** Gdzie kreska przestaje być
czytelna, jest oceną estetyczną, a `CLAUDE.md` §8 każe takich nie podejmować samemu.
Liczba jest wypisywana, żeby oglądający wiedział, czego się spodziewać.

**Co do `_normals` — pole „Skończone, gdy" żąda, żeby każda klatka „albo pokazywała
coś, co da się ocenić, albo miała zapisane, dlaczego nie może".** Ta klatka pokazuje
jeden bit: ciemno = przody, jasno = tyły. Da się to ocenić okiem i tak stoi w §5
(„przód ściany ciemny, tył jasny"), ale **od pustej klatki odróżnia ją wyłącznie
odcień**, nie treść. Jest to zapisane przy `proporcje_okna` i w docstringu materiału,
a liczba `tylna_strona=` stoi w logu przy każdym przebiegu.

## 5. Kontrole negatywne

Baza `test_camera_aim.py`: **24/24** (było 20). `__pycache__` czyszczony przed każdym
przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na trzech plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | podstawienie `center`/`size` przeniesione PO pierwszej kamerze | **23/24** |
| KN-2 | lista nazw kamer rozjechana z drzewem | **23/24** |
| KN-3 | proporcje liczone odwrotnie (wysokość ÷ długość) | **23/24** |
| KN-4 | zerowa wysokość przestaje być znoszona | **23/24**, dzielenie przez zero |
| KN-5 | wypis przestaje nazywać kamery | **23/24** |

KN-1 jest tu treścią: odtwarza dokładnie ten stan, który wpis pozycji przypisywał
dzisiejszemu kodowi. Po przeniesieniu podstawienia poniżej `add_camera` bramka mówi
„`center` jest podstawiany w wierszu 250, a pierwsza kamera powstaje w 234".

## 6. Weryfikacja

```
  24/24 przeszło        test_camera_aim.py   (było 20)
  2356/2356 przeszło, 123 moduły, KOD=0, RAZEM 169.883 s
```

Geometria: `tunnel_sweep.py` na `L1_A` → `wierzcholki=9520 sciany=8088 trojkaty=16176`,
`normalne_na_zewnatrz=0 zdegenerowane=0 nieskonczone=0`, `kontrole geometryczne: OK`.

## 7. Czego nie zrobiłem

* **Nie zmieniłem profilu tunelu ani liczby klatek** — oba wprost w „Poza zakresem".
* **Nie postawiłem progu na proporcjach.** Wymagałby oceny estetycznej; §8 każe wtedy
  zapytać, a pytanie tej pozycji brzmiało „które klatki okno zawęża", nie „kiedy kreska
  jest za cienka".
* **Nie zmieniłem podłogi pustej klatki**, choć pomiar pokazuje, że przepuszcza włos
  przy 924 : 1. Podłoga jest wspólna z pipeline'em wizualnym i jej zaostrzenie
  zapalałoby regresję wizualną na kadrach, które dziś przechodzą — to osobna pozycja
  i osobny pomiar.
* **Nie tknąłem nazw opcji.** `--from-m/--to-m` mówi prawdę: to jest okno kadru po osi,
  a nie „okno kamery wnętrza".
