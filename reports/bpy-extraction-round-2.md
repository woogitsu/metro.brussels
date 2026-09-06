# Druga runda wyciągania logiki spod `bpy` — nieosiągalne 53 → 24

**Zmierzone 06.09.2026 na commicie:** `3c01fbb`

`reports/mutation-sweep.md` nazwał lekarstwo wprost: „Lekarstwem tutaj nie są testy,
tylko dalsze wyciąganie logiki spod `bpy`". Pierwsza runda przeszła przez pięć modułów
(`m7_shell.py` 35 → 2, `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7,
`glb_roundtrip.py` 10 → 1, `place_vehicle.py` 7 → 1). Ta bierze trzy następne.

## 1. Mianownik — trzeci raz tego dnia trzeba go było ustalić przed pracą

Pozycja mówi „51 nieosiągalnych w 9 plikach" za raportem ze snapshotu `66b8301`.
Dziś, na **pełnym** zestawie pięciu klas operatorów, jest ich **350 w 10 plikach**.
Nie jest to regres: #258 rozszerzyło zestaw z dwóch klas na pięć i mianownik przestał
być ten sam.

Na **starym** zestawie (`--operators operator,prog`), czyli jedynym porównywalnym
z liczbą 51, wychodzi **53 w 9 plikach**. Ta liczba jest punktem wyjścia tego raportu
i to jej dotyczy kryterium „najwyżej 25".

## 2. Co zostało wyciągnięte

Wzorzec ten sam co przy poprzednich pięciu: moduł-rodzeństwo **bez** `import bpy`,
z którego skrypt sceny bierze gotowe wartości. W `tools/blender/` jest już trzynaście
takich modułów; dochodzą trzy.

| nowy moduł | z czego | co zawiera |
|---|---|---|
| `station_sections.py` | `station_kit.py` | `straight_prism`, `wall_offset_m`, `slab_sections`, `selected_platforms`, `side_tag`, `sweep_section` + założenia projektowe 2–4 |
| `marker_gates.py` | `detail_markers.py` | `select_marks`, `side_sign`, `clearance_problems` |
| `material_specs.py` | `material_test_scene.py` | `artefact_is_missing`, `is_transparent`, `is_glass`, `spec_id_problems` |

Skrypty scen biorą je pod **starymi nazwami**. Ekstrakcja nie zmieniła ani jednej
nazwy widocznej dla reszty pliku ani żadnego interfejsu CLI — te ostatnie wołają
bramki i pozycja wyklucza ich ruszanie.

| moduł | nieosiągalne przed | po |
|---|---:|---:|
| `station_kit.py` | 13 | **1** |
| `detail_markers.py` | 9 | **0** |
| `material_test_scene.py` | 12 | **4** |
| pozostałe sześć plików | 19 | 19 |
| **RAZEM** | **53** | **24** |

## 3. Pomyłka metody, która kosztowała dwie trzecie roboty

Najpierw sklasyfikowałem moduły po **funkcjach**: „czy gdziekolwiek w tej funkcji pada
`bpy`". Wynik brzmiał jednoznacznie i był w połowie fałszywy:

| moduł | mutacje w funkcjach „czystych" wg tej metody |
|---|---:|
| `station_kit.py` | 12 z 13 |
| `detail_markers.py` | 9 z 9 |
| `material_test_scene.py` | **0 z 12** |

Na tej podstawie ogłosiłem korektę zakresu pozycji: trzeci moduł jest nie do ruszenia,
sufit ekstrakcji to 21 z 34, do 25 się nie zejdzie.

Klasyfikacja po **wierszach, na których naprawdę siedzą mutacje**, dała co innego —
osiem z dwunastu:

```
w.199, w.257   os.path.getsize(path) <= 1024      4 mutacje
w. 66          float(spec.get("alpha", 1.0)) < 1.0  2
w. 86          spec["id"] == "glass"                1
w.222          len(ids) != len(set(ids))            1
```

Wszystkie cztery predykaty są zamurowane w funkcjach, które wołają Blendera, ale same
o nim nie wiedzą: sprawdzają rozmiar pliku, próg krycia w słowniku i duplikaty
w liście napisów.

**Wniosek na następną rundę:** granicą do przecięcia jest wiersz, nie funkcja. Podział
na „moduł czysty" i „moduł z `bpy`" jest zgrubny w obie strony — moduł czysty może
siedzieć pod `import bpy` i nie dać się przetestować, a moduł „z `bpy`" może niemal
w całości składać się z arytmetyki. Zapisane też w docstringu `material_specs.py`,
żeby następny czytający nie zaczynał od tej samej metody.

Nierozerwalne z Blenderem zostają cztery mutacje: `block.users == 0` (dwie) i
`obj.type == "MESH"` (dwie).

## 4. Dowód, że nie zmienił się ani jeden wierzchołek

Kryterium żąda, żeby GLB i PNG z bramek były identyczne z tymi sprzed ekstrakcji.
**W literze jest to nieosiągalne dla PNG** i sprawdziłem to, zanim cokolwiek zmieniłem:
dwa przebiegi `render_check.py` na tym samym `build/TEST.glb` dają trzy różne sumy
plików, bo Blender stempluje w każdym renderze `Date` i `RenderTime`. Piksele są
przy tym identyczne co do bajtu.

Stąd `tools/ci/png_pixels_sha256.py` — suma po sklejonych blokach `IDAT`, opisana
osobno w commicie `538db74`. Intencja kryterium jest w pełni sprawdzalna; zły był
przyrząd, nie zamiar.

Cztery odciski, przed i po ekstrakcji:

```
GLB       579e33ccdfac6a88…  =  579e33ccdfac6a88…
_iso      6b68351f28cd2961…  =  6b68351f28cd2961…
_side     42b3332a4f69bd3a…  =  42b3332a4f69bd3a…
_inside   ebb5396cd5fbb0ac…  =  ebb5396cd5fbb0ac…
```

Rendery obejrzane przed refaktorem (`CLAUDE.md` §5): `_iso` pokazuje łuk S z punktem
przegięcia, `_side` linię niemal poziomą z lekkim ugięciem, `_inside` wnętrze
prostokątnej rury z pierścieniami zbiegającymi się do punktu ucieczki — powierzchnia
lita, bez patrzenia „przez" ścianę. Po refaktorze sumy pikselowe są **te same**, więc
są to dosłownie te same obrazy; ponowne oglądanie niczego by nie dodało do sumy
kontrolnej.

## 5. Czego ta runda nie zrobiła

- **Nie dopisała testów wyciągniętym funkcjom.** Są teraz **osiągalne** dla przeglądu
  mutacyjnego i to jest cały cel pozycji; ile z nich przeżyje, powie dopiero pełny
  przebieg i będzie to materiał na osobny triaż, nie na tę pozycję.
- **Nie ruszyła `profile_vehicle.py` (7) ani `tunnel_sweep.py` (6)**, które są dziś
  największymi pozostałymi. Obie przeszły już pierwszą rundę; to, co w nich zostało,
  wymaga innego cięcia niż przeniesienie funkcji.
- **Nie zmieniła ani jednej linii w `render_check.py`.** Odcisk „po" ma sens tylko
  wtedy, gdy narzędzie mierzące jest to samo.

## 6. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1637/1637 przeszło

$ bash tools/ci/blender_smoke.sh
  [RESULT] T-010 automated smoke completed in 268s

$ sha256sum build/TEST.glb
  579e33ccdfac6a884a2dfcf86acca8bc256eed4af0e8603077b709c35eaf6bc9  build/TEST.glb

$ python3 tools/ci/png_pixels_sha256.py renders/TEST_*.png
  6b68351f…  renders/TEST_iso.png
  42b3332a…  renders/TEST_side.png
  ebb5396c…  renders/TEST_inside.png
```
