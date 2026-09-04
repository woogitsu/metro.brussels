# GLB bryły M7 nie jest powtarzalny między przebiegami — a siatka jest

**Zmierzone na commicie:** `2fa30c1`

Data: 03.09.2026. Znalezione przy okazji weryfikacji refaktoryzacji `m7_shell.py`.

## Objaw

Trzy przebiegi tego samego polecenia na **niezmienionym `main`**, tym samym
Blenderze 4.0.2, tej samej maszynie:

```
przebieg 1 na main: 155900 B  95d242897b7be01a
przebieg 2 na main: 155904 B  5acd093cf56a34a5
przebieg 3 na main: 154804 B  1b266ebccc31eec5
```

Różnica sięga 1,1 kB. `tunnel_sweep.py` w tych samych warunkach daje GLB
identyczny co do bajtu, więc to nie jest własność całego łańcucha.

## Co jest powtarzalne, a co nie

Raport JSON jest identyczny we wszystkich trzech przebiegach — po odjęciu
ścieżek i pola `bytes` porównanie wychodzi na równość. Wszystko, co mierzy
bramka, jest takie samo:

| | przebieg 1 | przebieg 2 | przebieg 3 |
|---|---|---|---|
| wierzchołki | 2334 | 2334 | 2334 |
| ściany | 1862 | 1862 | 1862 |
| bbox | `[0, -1.35, 0.95] .. [94, 1.35, 3.6]` | identycznie | identycznie |
| symetria obrotowa | ok, 0 niezgodnych | ok | ok |

Co więcej — **generator jest deterministyczny co do KOLEJNOŚCI wierzchołków**.
Sonda licząca sha256 z listy wierzchołków każdego obiektu, w kolejności, po
`build_shell()`, daje w dwóch przebiegach ten sam skrót dla wszystkich
jedenastu obiektów:

```
M7_car_1                 n=  453 w_kolejnosci=2270c33c064a4b7e posortowane=20f52e3f0cc27a3f
M7_car_2                 n=  312 w_kolejnosci=d2b144bd7b3364e2 posortowane=665bba25df3c4034
...
M7_articulation_5        n=   36 w_kolejnosci=06631b6df3ca85ac posortowane=9dd928e033130f19
```

## Wniosek

Niepowtarzalność **nie jest w kodzie tego projektu**. Siatka wychodzi
z `build_shell()` identyczna, z identyczną kolejnością wierzchołków; rozjeżdża
się dopiero to, co zapisuje `bpy.ops.export_scene.gltf`.

## Co z tego wynika dla weryfikacji

**Porównanie bajtowe GLB nie jest ważnym sygnałem dla `m7_shell.py`.** Refaktoryzację
tego pliku trzeba weryfikować raportem JSON (bez `path` i `bytes`) oraz skrótem
listy wierzchołków — jedno i drugie jest powtarzalne. Dla `tunnel_sweep.py`
porównanie bajtowe działa i zostaje.

Nie ma tu żadnej sugestii, że wynik jest zły: wszystkie kontrole geometryczne
przechodzą w każdym przebiegu. Jest tylko stwierdzenie, że **ten konkretny
plik nie nadaje się na baseline**.

## Czego NIE zrobiłem

Nie szukałem przyczyny wewnątrz eksportera glTF ani jej nie obchodziłem.
Sortowanie wierzchołków przed eksportem albo przypięcie innej wersji Blendera
to decyzje projektowe wykraczające poza refaktoryzację, przy której to wyszło.
