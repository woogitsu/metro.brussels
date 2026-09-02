# Kilometraż stacji był liczony na innej osi niż ta, która trafia do pliku

Stan: **2026-09-02**. Wyjście: `tools/track/build_alignment.py`, sześć plików
`data/track/*.json`, `tools/track/validate.py`, `tools/tests/test_validate_axis.py`.

---

## 1. Co się okazało

W #83 zgłosiłem, że rzut ostatniej stacji wypada 0,25–0,64 m **za** końcem osi, we
wszystkich sześciu pakietach. Opisałem to wtedy jako artefakt rzutowania punktu
przystanku na przedłużenie ostatniego odcinka. **Tak nie było.**

Po zmierzeniu dryfu na **każdej** stacji, nie tylko ostatniej, wyszedł obraz, który
mówi coś innego:

```
L1_A: Gare de l'Ouest    +0.000     ← pierwsza stacja: zero
      Beekkant           +0.010
      Étangs Noirs       +0.099
      Comte de Flandre   +0.140
      Sainte-Catherine   +0.258
      De Brouckère       +0.422
      Gare Centrale      +0.509
      Parc               +0.592
      Arts-Loi           +0.631
      Maelbeek           +0.629
      Schuman            +0.627
      Merode             +0.636     ← ostatnia stacja: maksimum
```

Dryf zaczyna się od zera i **narasta wzdłuż osi**, nie malejąc na żadnej stacji.
To nie jest artefakt na jednym końcu — to błąd rozkładający się na całą oś, w którym
ostatnia stacja jest po prostu najbardziej widocznym przypadkiem.

## 2. Przyczyna

`build_alignment.py` robi dwie rzeczy w tej kolejności:

1. tnie łamaną STIB między rzutami pierwszej i ostatniej stacji;
2. **przepróbkowuje** wycinek równomiernym krokiem 15 m, wymuszając trafienie
   w kotwice stacyjne (`resample_uniform`).

Przepróbkowanie ścina naroża, więc oś wynikowa jest **krótsza** od źródłowej. To jest
jawna transformacja i sam generator ją mierzy oraz raportuje.

Kilometraż stacji był natomiast liczony tak:

```python
"chainage_m": round(anchor["chainage"] - start, 2),   # kilometraż na łamanej ŹRÓDŁOWEJ
```

czyli na łamanej **przed** przepróbkowaniem — podczas gdy do pliku, do `points`, idzie
łamana **po** przepróbkowaniu. Dryf to skumulowana różnica długości między tymi dwiema.

### Generator już to liczył

To jest najbardziej niewygodna część tej diagnozy. `build_alignment.py` **od początku
mierzył tę różnicę i zapisywał ją do provenance**:

```python
"chord_shortfall_m": round(polyline_length(sliced) - chain_local[-1], 3),
```

a `data/track/*.provenance.json` nosi ją w każdym z sześciu pakietów:

| pakiet | `chord_shortfall_m` z provenance | dryf ostatniej stacji, zmierzony |
|---|---:|---:|
| L1_A | 0,635 | 0,64 |
| L1_B | 0,473 | 0,47 |
| L2_E | 0,552 | 0,55 |
| L5_C | 0,561 | 0,56 |
| L5_D | 0,254 | 0,25 |
| L6_F | 0,441 | 0,44 |

To ta sama wielkość — różnice na trzecim miejscu po przecinku to zaokrąglenie
`chainage_m` do centymetra. Generator raportował „ubytek na cięciwach" i wypisywał go
na konsolę przy każdym uruchomieniu, a mimo to używał kilometrażu sprzed przepróbkowania.
Liczba była na wierzchu, w pliku obok, i **nikt jej nie zestawił z kilometrażem stacji** —
łącznie ze mną, kiedy w #83 opisałem to jako artefakt rzutowania na końcu osi.

## 3. Dlaczego to więcej niż pół metra na końcu

Skoro dryf narasta, to **każda odległość międzystacyjna była zawyżona** o jego przyrost.
Nie o 0,64 m, tylko o różnicę dryfów na obu końcach odcinka:

| pakiet | stacji | maks dryf | maks zmiana odcinka | zmiana całości |
|---|---:|---:|---:|---:|
| L1_A | 12 | 0,640 m | 0,160 m | 0,640 m |
| L1_B | 9 | 0,470 m | 0,120 m | 0,470 m |
| L2_E | 17 | 0,550 m | 0,090 m | 0,550 m |
| L5_C | 9 | 0,560 m | 0,230 m | 0,560 m |
| L5_D | 7 | 0,250 m | 0,160 m | 0,250 m |
| L6_F | 7 | 0,440 m | 0,210 m | 0,440 m |

Te odległości są wejściem do T-113 (prędkości średnie rozkładowe), T-401 (porównanie
czasów jazdy z rozkładem) i koperty prędkości. Skala błędu jest mała — 0,09–0,23 m na
odcinku 300–1200 m, czyli poniżej 0,1 % — ale jest **systematyczna i w jedną stronę**,
a to jest dokładnie rodzaj błędu, który nie ujawnia się w żadnej sumie kontrolnej.

## 4. Poprawka

`resample_uniform` gwarantuje, że każda kotwica stacyjna **jest wierzchołkiem** osi
wynikowej — dostaje własny znacznik `station_anchor`. Kilometraż jest więc dostępny
dokładnie, bez przybliżeń: to skumulowana odległość do tego wierzchołka.

```python
anchor_indices = [i for i, (_p, tag) in enumerate(local) if tag == "station_anchor"]
if len(anchor_indices) != len(anchors):
    raise SystemExit(...)          # dwie stacje zlały się w jeden punkt
for anchor, index in zip(anchors, anchor_indices):
    anchor["axis_chainage"] = chain_local[index]
```

Kilometraż źródłowy nie znika — ląduje obok jako `source_chainage_m`, żeby dało się
**zmierzyć**, ile kosztuje przepróbkowanie, zamiast przyjmować to na wiarę.

**Geometria nie zmienia się wcale.** `points` i `length_m` są identyczne co do bajtu we
wszystkich sześciu plikach; zmieniają się wyłącznie liczby w tablicy `stations`.
Manifesty chunków, które odwołują się do `axis_length_m`, zostają ważne.

## 5. Weryfikacja — rzeczywiste wyjście

```
$ for P in A B C D E F; do python3 tools/track/build_alignment.py --package $P; done
$ python3 tools/tests/test_all.py
  421/421 przeszło

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 186, Skipped: 0, Total: 186

$ # ta sama pętla co w python-tests.yml
$ for axis in data/track/*.json; do python3 tools/track/validate.py "$axis" --line ...; done
sześć osi: kod 0

pakiet  stacji  maks dryf  maks Δodcinka   Δcałości  ostatnia poza osią
L1_A        12      0.640          0.160      0.640             -0.0036
L1_B         9      0.470          0.120      0.470             -0.0026
L2_E        17      0.550          0.090      0.550             -0.0013
L5_C         9      0.560          0.230      0.560             -0.0007
L5_D         7      0.250          0.160      0.250              0.0020
L6_F         7      0.440          0.210      0.440              -0.0002

geometria (points) i length_m identyczne we wszystkich sześciu plikach
```

Ostatnia kolumna to reszta po poprawce: **±4 mm**, i jest to wyłącznie zaokrąglenie
zapisu — `chainage_m` i `length_m` idą do pliku z dokładnością do centymetra.

## 6. Próg w walidatorze też był zły, tylko w drugą stronę

Po poprawce pakiet D zaczął zgłaszać przekroczenie **0,002 m**. Ostrzeżenie z #83
zapalało się przy `over > 0`, czyli przy każdej niezerowej różnicy — a plik zapisuje
kilometraż zaokrąglony do centymetra i **nie potrafi wyrazić zgodności dokładniejszej
niż centymetr**.

Próg jest teraz `LIMITS["length_tolerance_m"]` — dokładnie ta sama stała, którą ten
sam plik stosuje już do kontroli `length_m`, z tym samym uzasadnieniem.

## 7. Test-tripwire z #83 odwrócony, nie usunięty

`test_validate_every_package_axis_reports_the_overrun_it_actually_has` wymagał, żeby
wszystkie sześć osi zgłaszało przekroczenie — po to, żeby jego zniknięcie nie przeszło
niezauważone. Zniknęło jawnie, więc test **zmienia stronę, a nie ginie**:

- `test_validate_no_package_axis_overruns_its_own_end` — powrót przekroczenia znaczy,
  że kilometraż znowu rozjechał się z geometrią;
- `test_validate_last_station_lands_on_the_axis_end` — ostatnia stacja jest końcem osi,
  z tolerancją 1 cm;
- `test_validate_axes_keep_the_source_chainage_next_to_the_corrected_one` — `source_chainage_m`
  nie znika, a oś przepróbkowana nigdy nie wychodzi dłuższa od źródłowej.

## 8. Czego świadomie nie zrobiłem

- **Nie ruszyłem geometrii.** Kusiło, żeby przy okazji zmniejszyć krok przepróbkowania
  i zbić dryf u źródła — ale to zmiana wszystkich GLB, manifestów i progów gęstości,
  czyli osobne zadanie z własną weryfikacją.
- **Nie przeliczyłem raportów z poprzednich zadań.** `reports/L1_A-chunks.md` podaje
  granice chunków sprzed poprawki; różnią się teraz o do 0,64 m. Raporty są datowanym
  zapisem tego, co zmierzono wtedy, i nie poprawiam ich wstecz.
- **Nie zaktualizowałem liczb w T-113 ani T-401.** Odległości zmieniły się o mniej niż
  0,1 %, więc wnioski stoją, ale konkretne liczby w tamtych raportach są sprzed poprawki.
  Ponowny przebieg należy do scalenia #80 i #82, nie tutaj.

## 9. Co zauważyłem, ale nie tknąłem

- **Granice chunków przesuwają się o do 0,63 m**, bo leżą w połowie odległości między
  stacjami. Liczba chunków (12 dla pakietu A) i struktura zostają bez zmian; pipeline
  regeneruje je z osi, więc pozostaje spójny sam ze sobą.
- **Dryf nie narasta równomiernie.** W pakiecie A przyrosty na odcinek wahają się od
  +0,010 m do +0,160 m, a między Arts-Loi, Maelbeek i Schuman są zerowe — tam oś biegnie
  na tyle prosto, że przepróbkowanie nic nie ścina. To jest oczekiwane: dryf rośnie tam,
  gdzie są łuki, i stoi na prostych.

  Przy pełnej precyzji, przed zaokrągleniem do centymetra, na tych dwóch odcinkach wychodzi
  wahnięcie rzędu 2–4 mm w minus. **Nie nazywam tego wynikiem** — plik zapisuje kilometraż
  z dokładnością do centymetra, więc nie potrafi tego rozstrzygnąć, a przy tej skali nie
  odróżnię własności metody od błędu zaokrąglenia. Nowy test wymaga tylko, żeby suma dryfu
  nie wyszła ujemna.
