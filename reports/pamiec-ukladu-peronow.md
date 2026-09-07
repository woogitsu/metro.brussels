# Jeden moduł liczył to samo trzydzieści razy (6.B30)

**Zmierzone 07.09.2026 na commicie:** `ea68b7ca21ee842747d3b43c6fc3ffd8e8940f7f`
(gałąź `claude/6b30-pamiec-ukladu`).

## 1. Stan wyjściowy

`test_station_layout.py` zajmował **35,1 s** z ~100 s całego zestawu, przy 17 testach —
z czego cztery po ~6,0 s. Przyczyna: `_layout_for(axis_id)` czyta plik osi i woła
`SL.layout()` **bez żadnej pamięci**, a jest wołane z **pięciu** miejsc, każde w pętli
po **sześciu** osiach — czyli około trzydziestu pełnych przebiegów narzędzia na tych
samych sześciu plikach z `data/track/`.

## 2. Pytanie, które wpis kolejki zostawił otwarte — zmierzone, nie założone

Pamięć oddaje **ten sam obiekt** każdemu wołającemu. Test, który by go zmodyfikował,
psułby następny test w sposób **zależny od kolejności** — usterka gorsza od tych 35 s,
bo niewidoczna. Wpis 6.B30 mówił wprost, że to wymaga pomiaru, i pomiar poszedł
**przed** zmianą: sonda założyła pamięć, a po **każdym** z 17 testów policzyła odcisk
SHA-256 każdego zapamiętanego obiektu i porównała z odciskiem z chwili zapamiętania.

```
testow: 17, czas z pamiecia: 10.90 s
zapamietanych osi: 6  (bez pamieci bylo ~30 przebiegow)
testow, ktore ZMUTOWALY zapamietana strukture: 0
```

**Zero.** Sprawdzenie przez odcisk, a nie przez przeczytanie pięciu miejsc wołania:
odczyt kodu pokazuje `max`, `min`, `len`, `sum` i iterację, ale nie widzi mutacji
schowanej w funkcji pomocniczej ani w wyrażeniu, którego nie zauważyłem. Odcisk widzi
każdą.

Docstring funkcji mówi, co zrobić, gdyby to przestało być prawdą: kopia przy wydaniu
albo struktura niezmienna — **nie** zdjęcie pamięci, bo wtedy wracają trzydzieści
przebiegów.

## 3. Wynik

```
$ python3 tools/tests/test_all.py test_station_layout
  RAZEM 11.041 s, 17 testów, 1 modułów
kod: 0
```

Moduł: **35,1 s → 11,0 s**, czyli **3,2×**, przy niezmienionej liczbie testów (17)
i niezmienionym werdykcie.

Cały zestaw, trzy przebiegi z rzędu:

```
RAZEM 76.518 s, 1800 testów, 93 modułów
RAZEM 76.785 s, 1800 testów, 93 modułów
RAZEM 76.617 s, 1800 testów, 93 modułów
kod: 0
```

**105,3 s → 76,5 s** na tym samym hoście, ta sama liczba testów.

## 4. Kryterium „Skończone, gdy" NIE zostało spełnione — i to jest wynik pomiaru

Wpis żądał **poniżej 10 s**. Wyszło **11,0 s**. Liczba 10 s była moim **szacunkiem**
przy wpisywaniu pozycji do kolejki, nie pomiarem, i pomiar pokazuje, gdzie leży dno:

```
6.08 s  test_every_axis_clips_exactly_its_two_terminus_platforms
1.25 s  test_clipping_at_the_axis_ends_is_reported_not_hidden
1.22 s  test_minimum_edge_offset_is_half_width_plus_the_versine
1.19 s  test_profile_clearance_boundary_is_wider_than_the_geometric_minimum
```

Pierwszy z nich to **6,08 s wypełnienia pamięci**: jest pierwszym alfabetycznie testem
dotykającym wszystkich sześciu osi, więc płaci cały koszt sześciu przebiegów
`SL.layout`, po ~1 s każdy. Tej pracy nie da się usunąć — sześć układów trzeba
policzyć **raz**. Pozostałe ~5 s to testy na osiach **syntetycznych**, które
`_layout_for` nie wołają wcale, więc pamięć ich nie dotyczy.

Dno wynosi więc **~11 s**: 6 s nieusuwalnego wypełnienia + ~5 s testów syntetycznych.
Zejście poniżej 10 s wymagałoby **zmniejszenia tego, co testy liczą** — czyli
odebrania pokrycia, a nie przyspieszenia. Kryterium było za ostre; zmiana jest
skończona, a liczba w kryterium błędna, i to drugie mówię wprost, zamiast dopasować
raport do wpisu.

## 5. Czego świadomie nie zrobiono

- **`test_mutation_sweep.py` (16,4 s) i `test_curve_radius_axes.py` (14,0 s)** — pole
  „Poza zakresem". Inne przyczyny, każda osobną pracą.
- **Testów na osiach syntetycznych** (~5 s). Każdy liczy **inny** promień, więc pamięć
  na argumencie nic nie da; przyspieszenie wymagałoby zmiany tego, co sprawdzają.
- **Nie tknięto progu czasu zestawu.** To 6.D26 — ale ta zmiana **unieważnia liczby
  w jego wpisie**, więc wpis dostaje adnotację z nowym pomiarem. Kierunek pozostaje
  ten sam, tylko odwrócony: `MEASURED_MAX_WALL_S = 77.04` przestał być o 24 % niższy
  od rzeczywistości i jest jej teraz bliski (76,5–76,8 s), co znaczy, że margines
  progu 150 s wynosi ~1,96× — a nie że problem zniknął: **pomiar hosta pod
  obciążeniem nadal nie jest nigdzie zapisany**, i to jest treścią 6.D26.
