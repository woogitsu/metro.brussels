# Triaż ocalałych mutacji: `tools/track/build_alignment.py`, blok geometrii

Data: 03.09.2026. Wejście: przemiatanie mutacyjne z `tools/tests/mutation_sweep.py`.

## Stan przed i po

| | mutacji | ocalałych | zabitych |
|---|---:|---:|---:|
| przed | 69 | 57 | 12 |
| po | 69 | **39** | **30** |

W samym bloku geometrii (wiersze 65–261, funkcje czyste, bez shapefile'a):
**32 ocalałe → 15**, i każda z tych 15 ma werdykt **z pomiaru**, nie z czytania kodu.

## Jak klasyfikowałem

Nie pytałem „czy testy to zabijają". Pytałem: **czy istnieje JAKIEKOLWIEK wejście,
na którym zmutowana funkcja daje inny wynik niż oryginalna.** Narzędzie różnicowe
ładuje obie wersje modułu obok siebie i przepuszcza przez nie 68 łamanych
(8 ręcznie dobranych patologii plus 60 losowych z ustalonym ziarnem) razy pełną
siatkę wywołań `point_at`, `slice_polyline`, `project_on_polyline`, `densify`,
`_radius` i `resample_uniform` — łącznie ok. 40 tys. porównań na mutację.

Trzy możliwe odpowiedzi:

- **RÓŻNICA** — jest wejście, które je odróżnia. Mutacja jest zabijalna, brak testu.
- **MARTWE WYJŚCIE** — różni się wyłącznie etykieta pochodzenia ze `slice_polyline`,
  a tej nikt nie czyta. Klasa historyczna: etykiety zostały usunięte decyzją
  właściciela, więc te mutacje są dziś po prostu RÓWNOWAŻNE (patrz niżej).
- **RÓWNOWAŻNA** — żadne wejście nie odróżnia.

To nie jest formalny dowód równoważności. Jest to najmocniejsza rzecz, jaką umiem
zrobić bez dowodzenia, i jest o klasę mocniejsza od „przeczytałem i wygląda na
równoważną" — czyli od metody, którą **dwa razy w tej sesji się pomyliłem**.

### Kontrola samej metody: czy bateria w ogóle DOTKNĘŁA granicy

„Zero różnic" nie znaczy nic, dopóki nie wiadomo, czy bateria trafiła w punkty
równości — losowe wejścia z definicji w nie nie trafiają. Policzyłem więc trafienia
osobno, dla każdej granicy, na której orzekam:

| granica | trafień w baterii |
|---|---:|
| `t == 0.0` (domknięcie rzutu od dołu) | 15 |
| `t == 1.0` (domknięcie rzutu od góry) | 4 |
| `seg == 0` (segment zerowej długości) | 14 |
| `chainage == 0` | 68 |
| `chainage == chain[-1]` | 68 |
| `chainage` dokładnie w wierzchołku wewnętrznym | 4 |
| `span == 0` w `point_at` | 2 |
| `d == 0` w `_radius` (punkty współliniowe) | 8 |
| **`dist == 1e-9`** | **0** |

Ostatni wiersz był dziurą w metodzie: dla wierszy 119 i 121 bateria granicy
**nie dotykała**, więc pierwotny werdykt „równoważna, bo szczelina 1e-9 jest
nieosiągalna" był nieuzasadniony — szczelina JEST osiągalna, wystarczy podać
`end == chain[-1] - 1e-9`. Werdykt się obronił, ale z zupełnie innego powodu,
opisanego niżej.

## Co znalazło się przez pomiar, a nie dało czytać

Trzy mutacje, które uznałem za nieszkodliwe po przeczytaniu kodu, okazały się
zabijalne. Dwie z nich to ta sama, niespodziewana rzecz:

**`slice_polyline`: ostre `<` w warunkach cięcia to nie zakres, to zabezpieczenie
przed dzieleniem przez zero.**

```python
if c0 < start_chainage <= c1:                   # wiersz 113
    out.append((_lerp(a, b, (start_chainage - c0) / (c1 - c0)), ...))
```

Gdy oś ma zdublowany wierzchołek — a oś STIB ma — segment między kopiami spełnia
`c1 - c0 == 0`. Nieostry warunek wpuszcza go do interpolacji:

```
linia [(0,0), (50,0), (50,0), (100,0)],  slice(50, 75)
  oryginał: ((50.0, 0.0), (75.0, 0.0))
  mutant  : ZeroDivisionError
```

To samo od drugiej strony, wiersz 117 (`c0 <= end_chainage < c1`). Obie mutacje
przeżyły komplet testów sprzed tego triażu. Każda ma teraz własny test.

Trzecia: **`point_at` na dokładnym końcu osi**. Skrót `chainage >= chain[-1]`
zwraca ostatni wierzchołek; bez niego punkt idzie przez interpolację i wraca
z błędem narastającego `cumulative`:

```
oryginał: (359.20194920518566, 450.2239496826585)
mutant  : (359.2019492051856,  450.22394968265843)
```

Różnica to 1e-13 m — fizycznie nic. Ale kotwice stacji porównuje się z końcem osi
**na równość**, nie z tolerancją, więc gwarancją jest tożsamość, nie przybliżenie.
Test przypina konkretną łamaną, bo na krótkiej i prostej różnicy nie ma.

## Martwe wyjście `slice_polyline` — USUNIĘTE

**Właściciel zdecydował: etykiety znikają.** Poniższy opis zostaje jako zapis
tego, co i dlaczego było nie tak; sam kod już tego nie robi.

`slice_polyline` zwraca pary `(punkt, pochodzenie)`, gdzie pochodzenie to
`"source_vertex:<i>"` albo `"interpolated_cut"`. **Wszystkie cztery miejsca
w `build_alignment.py`, które ją wołają, robią `[p for p, _ in slice_polyline(...)]`
— etykieta jest odrzucana na wejściu.** Do `data/track/*.json` nie trafia; plik osi
nie ma per-punktowego `provenance` (ma go `resample_uniform`, i TAMTA etykieta
jest żywa i używana).

Cztery z pozostałych 15 ocalałych mutacji (110, 113, 115, 117) zmieniają
**wyłącznie tę etykietę**. Nie da się ich zabić testem, który broni czegoś
prawdziwego — można je zabić tylko przypinając wartości, na których nic nie stoi.

Wybrany został wariant „usunąć": `slice_polyline` zwraca same punkty. Wariant
„uruchomić" (przepisać pochodzenie do pliku osi) zmieniałby format
`data/track/*.json`, a `data/` jest tylko do odczytu (CLAUDE.md reguła 6).

**Skutek dla klasyfikacji:** cztery mutacje, które zmieniały wyłącznie etykietę,
NIE znikają z listy — to nadal są porównania i nadal się mutują. Zmienia się ich
werdykt: z „martwego wyjścia" na **prawdziwą równoważność**, bo po usunięciu
etykiet nie mają już czego zmienić. Sprawdzone wykonaniem po zmianie, osobno dla
każdego z dwóch wystąpień `<=` w wierszu 119: 780 i 768 porównań, **zero różnic**,
przy 402 cięciach trafiających dokładnie w wierzchołek.

## Pozostałe 15 ocalałych w bloku geometrii

| wiersz | mutacja | werdykt |
|---|---|---|
| 88 | `t < 0.0` → `<=` | RÓWNOWAŻNA — przy `t == 0` obie gałęzie dają 0.0 |
| 88 | `t > 1.0` → `>=` | RÓWNOWAŻNA — przy `t == 1` obie dają 1.0 |
| 110 | `c1 < start` → `<=` | RÓWNOWAŻNA (po usunięciu etykiet) |
| 113 | `start <= c1` → `<` | RÓWNOWAŻNA (po usunięciu etykiet) |
| 115 | `c0 <= end` → `<` | RÓWNOWAŻNA (po usunięciu etykiet) |
| 117 | `c0 <= end` → `<` | RÓWNOWAŻNA |
| 119 | `end >= chain[-1] - 1e-9` → `>` | RÓWNOWAŻNA — próg nanometrowy jest zdominowany przez dedupikację mikrometrową (niżej) |
| 121 | `dist > 1e-9` → `>=` | RÓWNOWAŻNA — jw. |
| 121 | próg `1e-9` → `1.01e-9` | RÓWNOWAŻNA — jw. |
| 138 | `chainage <= 0` → `<` | RÓWNOWAŻNA — przy 0 pętla i tak zwraca `points[0]` |
| 143 | `chain[i] <= c` → `<` | RÓWNOWAŻNA — sąsiedni segment łapie ten sam punkt |
| 143 | `c <= chain[i+1]` → `<` | RÓWNOWAŻNA — jw. |
| 145 | `span <= 0` → `<` | RÓWNOWAŻNA — `span == 0` jest nieosiągalne, bo wcześniejszy segment zawsze dopasuje się pierwszy |
| 221 | `abs(d) < 1e-9` → `<=` | RÓWNOWAŻNA — punkty współliniowe dają `d == 0` dokładnie |
| 221 | próg `1e-9` → `1.01e-9` | RÓWNOWAŻNA — jw. |

### Próg nanometrowy jest martwy wobec mikrometrowego

Warunek `math.dist(out[-1][0], last) > 1e-9` przy domknięciu prawego końca decyduje
wyłącznie o punktach leżących o mniej niż 1e-9 od poprzednika. Każdy taki punkt jest
zaraz potem usuwany przez dedupikację, która skleja wszystko bliżej niż **1e-6**.
Trzy mutacje w wierszach 119 i 121 nie mają więc jak się objawić — nie dlatego, że
granica jest nieosiągalna, tylko dlatego, że za nią stoi próg tysiąc razy szerszy.

Sprawdzone wykonaniem na ośmiu wejściach trafiających DOKŁADNIE w granicę
(`end == chain[-1] - 1e-9` dla trzech długości osi oraz łamane, których ostatni
segment ma 1e-9), dla trzech mutacji naraz: **zero różnic**. Jest na to test
`test_alignment_the_nanometre_guard_is_dominated_by_the_micrometre_dedup`.

To jest zarazem znalezisko projektowe: **strażnik 1e-9 nie robi nic**. Nie usuwam go,
bo jego usunięcie zmienia czytelność, nie zachowanie, a decyzja należy do właściciela.

### Martwa granica w żywym warunku

Zwracam uwagę na wiersz 145: `if span <= 0: return points[index]` **nigdy się nie
wykonuje**, bo dla kilometrażu równego zdublowanemu wierzchołkowi wcześniejszy
segment dopasowuje się pierwszy i kończy funkcję. Sam próg jest za to żywy —
mutacja `0 → 1` ginie, bo zamieniłaby interpolację na skok do wierzchołka
w segmentach krótszych niż metr, a takie w łukach STIB są. To nie jest martwy
warunek do usunięcia, tylko martwa **granica** wewnątrz żywego warunku.

## Czego ten triaż NIE objął

24 ocalałe mutacje w wierszach 347–794 — `resolve_source`, `pick_stops`,
`crosscheck`, budowa raportu. Wymagają zaczepu z prawdziwego shapefile'a STIB
albo jego atrapy o pełnej strukturze; to osobne zadanie, nie dopisek do tego.
