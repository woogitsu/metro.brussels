#!/usr/bin/env python3
"""Testy jednostkowe transformacji współrzędnych (`tools/track/crs.py`).

**Dlaczego ten plik powstał.** `crs.py` nie ma pliku testów własnych. Jedyny plik
nazwany po nim, `test_crs_convergence.py`, sam deklaruje w pierwszym zdaniu, co
sprawdza: „Niezbieżność w `tools/track/crs.py` musi być słyszalna" — czyli JEDNĄ
własność. Poza nią moduł jest dotykany przez `test_alignment.py` (trzy punkty
odniesienia i round-trip) oraz przez kontrole całych pakietów, a to jest pomiar
wyniku całego łańcucha, nie granic pojedynczych funkcji.

Zmierzone przemiataniem mutacyjnym na `ee84432`:

    python3 tools/tests/mutation_sweep.py --only tools/track/crs.py --workers 4
    [MUTACJE] rozstrzygniętych 14/14, zabitych 6, ocalałych 8, nierozstrzygniętych 0
      OCALAŁA  tools/track/crs.py:152 prog `0.0` -> `0.001`
      OCALAŁA  tools/track/crs.py:152 operator `>=` -> `>`
      OCALAŁA  tools/track/crs.py:163 operator `<` -> `<=`
      OCALAŁA  tools/track/crs.py:172 operator `>` -> `>=`
      OCALAŁA  tools/track/crs.py:300 prog `1e-12` -> `1.01e-12`
      OCALAŁA  tools/track/crs.py:300 operator `<` -> `<=`
      OCALAŁA  tools/track/crs.py:419 prog `1e-12` -> `1.01e-12`
      OCALAŁA  tools/track/crs.py:419 operator `<` -> `<=`

Osiem na czternaście, 57 % — najgorszy udział wśród modułów bez pliku testów
własnych, po `make_test_track.py`.

Ten plik bierze cztery z tych ośmiu: wybór półkuli w gałęzi osi obrotu (152, dwie
mutacje), kryterium zbieżności iteracji ECEF (163) i próg residuum (172).

Cztery pozostałe — progi `1e-12` w wierszach 300 i 419 — są **nieosiągalne z API**
i to jest kwalifikacja „mutant równoważny" z `reports/mutation-sweep.md`, a nie
dziura do załatania. Dla wiersza 419 pomiar stoi już w
`test_alignment.py::test_crs_laea_origin_is_the_only_point_taking_the_degenerate_branch`
(najmniejszy niezerowy `rho` to ok. 4,7e-10, czyli 466 razy próg) i ten plik go
NIE powtarza. Dla wiersza 300 takiego pomiaru nie było nigdzie i dokłada go
ostatni test tutaj.

Technika dla granic dokładnych jest ta sama, co w `test_crs_convergence.py`: progu
nie da się trafić dodawaniem, więc próg jest **odczytywany z wnętrza funkcji** —
raz z komunikatu wyjątku (`repr`, czyli bit w bit), raz z powtórzonego jednego
obrotu pętli. Bez tego test przechodziłby identycznie dla `<` i dla `<=`.
"""
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import crs as CRS  # noqa: E402

#: `_ecef_to_geodetic` zapisuje residuum przez `repr`, więc `float()` odtwarza je co do bitu.
RESIDUAL_IN_MESSAGE = re.compile(r"residuum (\S+) m przekracza")

#: Półoś mała WGS84 — biegun leży dokładnie na niej.
SEMI_MINOR = CRS.A_WGS * (1 - CRS.F_WGS)

#: Punkt 6000 km pod Brukselą. Iteracja ECEF potrzebuje tam 14 obrotów (nagłówek
#: `_ecef_to_geodetic`), więc kolejne iteraty są jeszcze daleko od siebie i różnicę
#: między „przerwij teraz" a „przerwij o obrót później" widać w trzeciej cyfrze.
DEEP = CRS._geodetic_to_ecef(4.35, 50.85, CRS.A_WGS, CRS.F_WGS, -6_000_000.0)


# --- wiersz 152: która półkula, gdy punkt leży na osi obrotu ---------------------

def test_crs_axis_branch_at_z_exactly_zero_answers_north_not_south():
    """`lat_deg = 90.0 if z >= 0.0 else -90.0` — zero należy do PÓŁNOCY.

    Istniejące testy gałęzi osi podają `z = ±b`, czyli nigdy nie dotykają granicy.
    Obie mutacje tego wiersza (`>=` -> `>` oraz próg `0.0` -> `0.001`) zamieniają
    dla `z = 0.0` biegun północny na południowy i przechodziły całą suitę.

    `x = y = z = 0` to środek Ziemi: `p` jest zerem, więc gałąź osi się włącza,
    a wysokość liczy się wprost jako `|z| - b`. Round-trip wychodzi tu z residuum
    2,6e-12 m, czyli odpowiedź jest współrzędną, a nie zapchajdziurą.
    """
    lon, lat, height = CRS._ecef_to_geodetic(0.0, 0.0, 0.0, CRS.A_WGS, CRS.F_WGS)
    assert lat == 90.0, lat
    assert lon == 0.0, lon
    assert height == -SEMI_MINOR, (height, -SEMI_MINOR)
    residual = CRS.ecef_to_geodetic_residual_m(0.0, 0.0, 0.0, CRS.A_WGS, CRS.F_WGS)
    assert residual < 1e-9, residual


def test_crs_axis_branch_flips_at_the_first_float_below_zero():
    """Kontrola negatywna do poprzedniego: granica ma być DOKŁADNIE w zerze.

    Najmniejszy float poniżej zera (`nextafter(0.0, -1.0)`, czyli -5e-324) daje już
    południe, a `-0.0` — które w IEEE 754 spełnia `>= 0.0` — nadal północ. Gdyby
    granica stała gdziekolwiek indziej (mutacja progu przesuwa ją na 0,001 m),
    jedna z tych trzech odpowiedzi byłaby inna.
    """
    def latitude(z):
        return CRS._ecef_to_geodetic(0.0, 0.0, z, CRS.A_WGS, CRS.F_WGS)[1]

    assert latitude(-0.0) == 90.0, latitude(-0.0)
    assert latitude(math.nextafter(0.0, -1.0)) == -90.0, latitude(math.nextafter(0.0, -1.0))
    assert latitude(math.nextafter(0.0, 1.0)) == 90.0, latitude(math.nextafter(0.0, 1.0))
    # Milimetr nad zerem — po tej samej stronie, ale już poza progiem 0,001 m,
    # który podstawia mutacja. Bez tego punktu próg dałoby się przesunąć niezauważenie.
    assert latitude(0.0005) == 90.0, latitude(0.0005)


# --- wiersz 172: residuum dokładnie na progu jest jeszcze współrzędną ------------

def test_crs_ecef_residual_exactly_at_the_threshold_is_accepted():
    """`residual_m > max_residual_m` — równość PRZECHODZI, mutacja `>=` ją odrzuca.

    Progu nie da się trafić z zewnątrz, więc idzie to odwrotnie, tak samo jak
    w `test_crs_convergence.py`: funkcja jest najpierw pytana o residuum, jakie
    faktycznie osiąga, a odczytana z komunikatu liczba wraca jako `max_residual_m`.
    Komunikat zapisuje ją przez `repr`, więc `float()` odtwarza ją co do bitu.

    Wejście: milimetr od osi obrotu, przy `z` na powierzchni — punkt, dla którego
    nagłówek modułu podaje residuum 1,4 m i który przy domyślnym progu 1,0 m jest
    odrzucany.
    """
    near_axis = (1e-3, 0.0, SEMI_MINOR)
    try:
        CRS._ecef_to_geodetic(*near_axis, CRS.A_WGS, CRS.F_WGS)
        raise AssertionError("residuum 1,4 m przy progu 1,0 m nie może przejść")
    except ValueError as error:
        reached = float(RESIDUAL_IN_MESSAGE.search(str(error)).group(1))
    assert reached > CRS.MAX_ECEF_RESIDUAL_M, (reached, CRS.MAX_ECEF_RESIDUAL_M)

    # residuum == max_residual_m, bit w bit -> przechodzi
    lon, lat, height = CRS._ecef_to_geodetic(*near_axis, CRS.A_WGS, CRS.F_WGS,
                                             max_residual_m=reached)
    assert lat == 89.99999999104696, lat
    assert lon == 0.0, lon
    assert height == -reached, (height, reached)

    # pierwszy float PONIŻEJ progu -> odmowa, i to z tym samym residuum
    try:
        CRS._ecef_to_geodetic(*near_axis, CRS.A_WGS, CRS.F_WGS,
                              max_residual_m=math.nextafter(reached, -math.inf))
    except ValueError as error:
        assert float(RESIDUAL_IN_MESSAGE.search(str(error)).group(1)) == reached, str(error)
    else:
        raise AssertionError(f"residuum {reached!r} m ponad progiem powinno być odmową")


def test_crs_ecef_threshold_default_is_the_declared_datum_accuracy():
    """Kontrola do poprzedniego: próg domyślny to `MAX_ECEF_RESIDUAL_M`, nie liczba
    dobrana pod test. Gdyby ktoś rozluźnił stałą, test wyżej dalej by przechodził."""
    import inspect
    default = inspect.signature(CRS._ecef_to_geodetic).parameters["max_residual_m"].default
    assert default == CRS.MAX_ECEF_RESIDUAL_M == 1.0, (default, CRS.MAX_ECEF_RESIDUAL_M)


# --- wiersz 163: krok równy tolerancji to jeszcze nie zbieżność ------------------

def _first_ecef_step(x, y, z, a, f):
    """Pierwszy obrót pętli z `_ecef_to_geodetic`, powtórzony co do bitu.

    Funkcja nie zgłasza długości swojego kroku żadnym komunikatem, więc drogi
    „odczytaj próg z wyjątku" tu nie ma. Zostaje druga: powtórzyć jeden obrót
    tymi samymi działaniami w tej samej kolejności. Że to jest ta sama rachuba,
    a nie przybliżenie, sprawdza asercja w teście niżej — wynik repliki musi być
    IDENTYCZNY z tym, co funkcja zwraca po dokładnie jednej iteracji.
    """
    e2 = f * (2 - f)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))
    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    h = p / math.cos(lat) - n
    step = math.atan2(z, p * (1 - e2 * n / (n + h)))
    return lat, step


def test_crs_ecef_step_exactly_at_the_tolerance_is_not_convergence():
    """`abs(step - lat) * a < tolerance_m` — równość NIE kończy iteracji.

    Mutacja `<` -> `<=` przerywa pętlę o jeden obrót wcześniej. Przy zwykłym
    wejściu jest to niewidoczne, bo iteracja i tak dochodzi do tego samego punktu
    stałego; widać to dopiero wtedy, gdy tolerancja jest równa co do bitu długości
    PIERWSZEGO kroku, a wejście potrzebuje ich czternastu.

    `max_residual_m` jest tu wyłączone celowo: mierzona jest liczba obrotów, a nie
    bramka residuum, która przy wyniku po jednym czy dwóch obrotach odezwałaby się
    pierwsza i zasłoniła pomiar.
    """
    lat0, step1 = _first_ecef_step(*DEEP, CRS.A_WGS, CRS.F_WGS)
    tolerance = abs(step1 - lat0) * CRS.A_WGS

    after_one = CRS._ecef_to_geodetic(*DEEP, CRS.A_WGS, CRS.F_WGS, tolerance_m=0.0,
                                      iterations=1, max_residual_m=math.inf)[1]
    after_two = CRS._ecef_to_geodetic(*DEEP, CRS.A_WGS, CRS.F_WGS, tolerance_m=0.0,
                                      iterations=2, max_residual_m=math.inf)[1]
    # Replika jest tą samą rachubą, a nie przybliżeniem — inaczej `tolerance` nie
    # byłoby granicą, tylko liczbą obok niej.
    assert math.degrees(step1) == after_one, (math.degrees(step1), after_one)
    assert after_one != after_two, (after_one, after_two)

    got = CRS._ecef_to_geodetic(*DEEP, CRS.A_WGS, CRS.F_WGS, tolerance_m=tolerance,
                                max_residual_m=math.inf)[1]
    assert got == after_two, (got, after_two, after_one)
    assert got != after_one, "krok równy tolerancji przerwał pętlę — to jest `<=`, nie `<`"

    # Kontrola w drugą stronę: pierwszy float POWYŻEJ tej samej tolerancji już
    # przerywa po pierwszym obrocie. Granica leży więc dokładnie tam, gdzie ma.
    above = CRS._ecef_to_geodetic(*DEEP, CRS.A_WGS, CRS.F_WGS,
                                  tolerance_m=math.nextafter(tolerance, math.inf),
                                  max_residual_m=math.inf)[1]
    assert above == after_one, (above, after_one)


def test_crs_ecef_deep_point_still_lands_on_brussels_when_left_to_converge():
    """Kontrola, że wejście z testu wyżej jest sensowne, a nie samym patologicznym
    przypadkiem: bez podstawionej tolerancji ten sam punkt wraca na 4,35/50,85."""
    lon, lat, height = CRS._ecef_to_geodetic(*DEEP, CRS.A_WGS, CRS.F_WGS)
    assert abs(lon - 4.35) < 1e-12, lon
    assert abs(lat - 50.85) < 1e-12, lat
    assert abs(height + 6_000_000.0) < 1e-6, height


# --- wiersz 300: próg `1e-12`, którego z API nie da się dotknąć ------------------

def test_crs_lambert_jacobian_never_comes_near_its_degenerate_gate():
    """Ten sam powód dla dwóch mutacji wiersza 300, i ten sam rodzaj pomiaru.

    `abs(determinant) < 1e-12` w `lambert72_to_wgs84` bramkuje jakobian 2x2 liczony
    różnicami skończonymi z krokiem 1e-7 stopnia. Wyznacznik ma tam wymiar
    (m/deg)², czyli rząd 1e10 w środku sieci. Zmierzone tą samą rachubą, co
    w funkcji:

        4,35°E 50,85°N (środek sieci)  ->  7,83e+09
        4,35°E 89°N                    ->  9,32e+08
        4,35°E 89,999°N                ->  1,56e+07
        4,35°E 89,99999°N              ->  1,72e+05

    Do bieguna odwzorowania wyznacznik schodzi skokiem do zera, a nie przez pasmo
    [1e-12, 1,01e-12) — i tam gałąź włącza się jednakowo przed mutacją i po niej,
    bo `0 < 1e-12` i `0 < 1,01e-12` są tak samo prawdziwe. Mutacje wiersza 300 są
    więc równoważne z tego samego powodu, co te z wiersza 419 (patrz
    `test_alignment.py::test_crs_laea_origin_is_the_only_point_taking_the_degenerate_branch`);
    ten test zapisuje liczby, na których to stoi.
    """
    def determinant(lon, lat):
        h = 1e-7
        fx, fy = CRS.wgs84_to_lambert72(lon, lat)
        x_lon, y_lon = CRS.wgs84_to_lambert72(lon + h, lat)
        x_lat, y_lat = CRS.wgs84_to_lambert72(lon, lat + h)
        j11, j21 = (x_lon - fx) / h, (y_lon - fy) / h
        j12, j22 = (x_lat - fx) / h, (y_lat - fy) / h
        return j11 * j22 - j12 * j21

    measured = [(50.85, 7.8e9), (89.0, 9.3e8), (89.999, 1.5e7), (89.99999, 1.7e5)]
    for latitude, expected in measured:
        value = abs(determinant(4.35, latitude))
        assert value > 1e4, (latitude, value)
        assert 0.9 * expected < value < 1.2 * expected, (latitude, value, expected)

    # Najmniejszy zmierzony wyznacznik jest ponad szesnaście rzędów wielkości nad
    # bramką — pasmo, w którym mutacja progu cokolwiek by zmieniła, jest puste.
    assert abs(determinant(4.35, 89.99999)) / 1e-12 > 1e16
