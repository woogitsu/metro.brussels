"""WGS84 <-> EPSG:31370 (BD72 / Belgian Lambert 72) — czysty stdlib.

Projekt nie ma manifestu zależności, a CI odpala goły `python3`, więc transformacja
musi działać bez pyproj i bez GDAL.

Parametry odwzorowania odpowiadają dokładnie plikowi `.prj` shapefile'ów STIB
(`ACTU_LIGNES_BRUTES.prj`, `Belge_Lambert_1972`) i rejestrowi EPSG:31370.
Transformacja datum używa EPSG:15929 (`BD72 to WGS 84 (3)`) w pełnej precyzji.

Kontrola dokładności wobec PROJ 9 / pyproj 3.7 (biblioteki użytej wyłącznie do
weryfikacji, nie jako zależność):

- sama projekcja Lambert Conformal Conic 2SP: zgodność **0,000 mm**;
- pełny łańcuch WGS84 -> EPSG:31370 przy identycznych parametrach: **0,25 mm**;
- round-trip tej implementacji: **1 nm**.

Reszta różnicy wobec domyślnego potoku PROJ bierze się stąd, że baza EPSG w PROJ
trzyma parametry Helmerta zaokrąglone do czterech miejsc (`ry=0.457` zamiast
`0.456955`). Sama transformacja BD72<->WGS84 jest w EPSG opisana jako
`VERSION["IGN-Bel 1m"]`, czyli ma **deklarowaną dokładność 1 metr** — żadna
implementacja nie uczyni jej dokładniejszą i nie wolno na jej podstawie twierdzić,
że oś ma dokładność milimetrową.
"""
import math

A_WGS, F_WGS = 6378137.0, 1.0 / 298.257223563
A_BD72, F_BD72 = 6378388.0, 1.0 / 297.0

# EPSG:15929 BD72 -> WGS84, position vector, 7 parametrów
DX, DY, DZ = -106.868628, 52.297783, -103.723893
RX = math.radians(0.336570 / 3600.0)
RY = math.radians(-0.456955 / 3600.0)
RZ = math.radians(1.842183 / 3600.0)
DS = -1.2747e-6

# EPSG:31370 Lambert Conformal Conic 2SP
PHI_F = math.radians(90.0)
LAM_F = math.radians(4.36748666666667)
PHI_1 = math.radians(51.1666672333333)
PHI_2 = math.radians(49.8333339)
E_F, N_F = 150000.013, 5400088.438


def _geodetic_to_ecef(lon, lat, a, f, h=0.0):
    e2 = f * (2 - f)
    p, l = math.radians(lat), math.radians(lon)
    n = a / math.sqrt(1 - e2 * math.sin(p) ** 2)
    return ((n + h) * math.cos(p) * math.cos(l),
            (n + h) * math.cos(p) * math.sin(l),
            (n * (1 - e2) + h) * math.sin(p))


def _ecef_to_geodetic(x, y, z, a, f):
    e2 = f * (2 - f)
    l = math.atan2(y, x)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(12):
        n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1 - e2 * n / (n + h)))
    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    return math.degrees(l), math.degrees(lat), p / math.cos(lat) - n


def _helmert(x, y, z, dx, dy, dz, rx, ry, rz, ds):
    """Position vector: [X']=T+(1+s)*R*[X], R z małymi kątami."""
    return (dx + (1 + ds) * (x - rz * y + ry * z),
            dy + (1 + ds) * (rz * x + y - rx * z),
            dz + (1 + ds) * (-ry * x + rx * y + z))


def _bd72_to_wgs84_ecef(x, y, z):
    return _helmert(x, y, z, DX, DY, DZ, RX, RY, RZ, DS)


def _wgs84_to_bd72_ecef(xw, yw, zw):
    """Dokładna odwrotność Helmerta przez iterację.

    Negowanie parametrów jest tylko przybliżeniem pierwszego rzędu i zostawia
    systematyczne ~1,5 mm; iteracja schodzi do precyzji maszynowej.
    """
    x, y, z = xw - DX, yw - DY, zw - DZ
    for _ in range(6):
        fx, fy, fz = _bd72_to_wgs84_ecef(x, y, z)
        x += xw - fx
        y += yw - fy
        z += zw - fz
    return x, y, z


def wgs84_to_bd72(lon, lat, h=0.0):
    x, y, z = _geodetic_to_ecef(lon, lat, A_WGS, F_WGS, h)
    x, y, z = _wgs84_to_bd72_ecef(x, y, z)
    return _ecef_to_geodetic(x, y, z, A_BD72, F_BD72)


def _lcc_constants():
    e = math.sqrt(F_BD72 * (2 - F_BD72))

    def m(p): return math.cos(p) / math.sqrt(1 - e ** 2 * math.sin(p) ** 2)

    def t(p): return math.tan(math.pi / 4 - p / 2) / ((1 - e * math.sin(p)) / (1 + e * math.sin(p))) ** (e / 2)

    n = (math.log(m(PHI_1)) - math.log(m(PHI_2))) / (math.log(t(PHI_1)) - math.log(t(PHI_2)))
    big_f = m(PHI_1) / (n * t(PHI_1) ** n)
    r_f = A_BD72 * big_f * t(PHI_F) ** n
    return e, n, big_f, r_f, m, t


def bd72_to_lambert72(lon, lat):
    e, n, big_f, r_f, _m, t = _lcc_constants()
    p, l = math.radians(lat), math.radians(lon)
    r = A_BD72 * big_f * t(p) ** n
    theta = n * (l - LAM_F)
    return E_F + r * math.sin(theta), N_F + r_f - r * math.cos(theta)


def wgs84_to_lambert72(lon, lat, h=0.0):
    blon, blat, _ = wgs84_to_bd72(lon, lat, h)
    return bd72_to_lambert72(blon, blat)


# Środek brukselskiej sieci metra; punkt startowy iteracji, nie parametr odwzorowania.
LAMBERT_INVERSE_SEED = (4.35, 50.85)


def lambert72_to_wgs84(x, y, tolerance_m=1e-6, iterations=60):
    """Odwrotność `wgs84_to_lambert72`, policzona numerycznie (Newton 2x2).

    Analityczna inwersja wymagałaby odwrócenia zarówno odwzorowania LCC, jak i
    Helmerta BD72->WGS84 z tymi samymi parametrami; zamiast dublować tę algebrę
    (i ryzykować, że obie gałęzie się rozjadą) odwracamy istniejącą funkcję w
    przód. Residuum jest **mierzone**: `residual_m()` mówi, o ile powrót do
    Lamberta rozmija się z punktem wejściowym, a test sprawdza podmilimetrową
    zgodność na całej brukselskiej sieci.

    Potrzebne tam, gdzie z osi w Lambercie 72 trzeba zbudować zapytanie do
    źródła w WGS84 (OSM, UrbIS) — czyli w kontroli krzyżowej pakietów.

    **Niezbieżność jest błędem, nie wynikiem.** Wcześniej funkcja po wyczerpaniu
    `iterations` zwracała ostatni iterat bez słowa: dla `(1e9, 1e9)` była to
    szerokość -46040,3° przy residuum 9,98e+08 m na składową (1,41e+09 m
    euklidesowo), a dla bieguna odwzorowania długość 395,8° przy 2433 m na
    składową (2435 m euklidesowo). Rozjeżdżało to całą geometrię, bo
    residuum mierzy osobna funkcja `lambert_inverse_residual_m`, której nikt nie
    wołał. Teraz brak zbieżności podnosi `ValueError` — tą samą konwencją, co
    zdegenerowany jakobian poniżej, żeby wołający miał jeden wzorzec obsługi.

    Kryterium zbieżności jest **na składową i ostre**: `max(|dx|, |dy|)` musi być
    *mniejsze* od `tolerance_m`. Residuum równe dokładnie `tolerance_m` jest więc
    porażką, nie sukcesem — dokładnie jak w warunku przerwania pętli, którego ta
    zmiana nie rusza. Uwaga: `lambert_inverse_residual_m` mierzy odległość
    **euklidesową**, więc jej wynik może być do sqrt(2) raza większy od progu
    i to nie jest sprzeczność.

    Residuum w komunikacie jest zapisane przez `repr`, żeby dało się je odczytać
    z powrotem bez straty bitów — na tym opiera się test progu.
    """
    lon, lat = LAMBERT_INVERSE_SEED
    for _ in range(iterations):
        fx, fy = wgs84_to_lambert72(lon, lat)
        dx, dy = fx - x, fy - y
        if abs(dx) < tolerance_m and abs(dy) < tolerance_m:
            return lon, lat
        h = 1e-7
        x_lon, y_lon = wgs84_to_lambert72(lon + h, lat)
        x_lat, y_lat = wgs84_to_lambert72(lon, lat + h)
        j11, j21 = (x_lon - fx) / h, (y_lon - fy) / h
        j12, j22 = (x_lat - fx) / h, (y_lat - fy) / h
        determinant = j11 * j22 - j12 * j21
        if abs(determinant) < 1e-12:
            raise ValueError(f"inwersja Lamberta rozbieżna w punkcie {x}, {y}")
        lon -= (dx * j22 - dy * j12) / determinant
        lat -= (dy * j11 - dx * j21) / determinant
    fx, fy = wgs84_to_lambert72(lon, lat)
    residual_m = max(abs(fx - x), abs(fy - y))
    if residual_m < tolerance_m:
        return lon, lat
    raise ValueError(
        f"inwersja Lamberta rozbieżna w punkcie {x}, {y}: "
        f"residuum {residual_m!r} m nie zeszło pod tolerancję {tolerance_m!r} m "
        f"po {iterations} iteracjach")


def lambert_inverse_residual_m(x, y):
    """O ile metrów powrót przez `wgs84_to_lambert72` rozmija się z punktem wejścia."""
    lon, lat = lambert72_to_wgs84(x, y)
    bx, by = wgs84_to_lambert72(lon, lat)
    return math.dist((bx, by), (x, y))


# --- EPSG:3035 (ETRS89-extended / LAEA Europe) --------------------------------
#
# INSPIRE publikuje sieć szynową STIB w EPSG:3035, więc bez tej pary funkcji plik
# `TN.RailTransportNetwork.gml` jest nieporównywalny z osią w Lambercie 72.
#
# Elipsoida GRS80, początek 52°N/10°E, przesunięcia 4 321 000 / 3 210 000 m —
# parametry wpisane wprost w rejestr EPSG i powtórzone w `srsName` każdej geometrii
# tego datasetu.
#
# ETRS89 jest tu traktowane jak WGS84. To **przybliżenie, nie tożsamość**: oba układy
# rozjeżdżają się o ~2,5 cm rocznie od 1989 r. wskutek ruchu płyty euroazjatyckiej,
# czyli o rząd 0,8 m w 2026 r. Dla pomiaru *różnicy* dwóch geometrii z tego samego
# pliku błąd znosi się do zera; dla porównania z osią z innego źródła jest to
# systematyczne przesunięcie całej chmury i tak trzeba je opisywać.

A_GRS80, F_GRS80 = 6378137.0, 1.0 / 298.257222101
LAEA_LAT0 = math.radians(52.0)
LAEA_LON0 = math.radians(10.0)
LAEA_FE, LAEA_FN = 4321000.0, 3210000.0


def _laea_q(sin_phi, e):
    """Pole autalicznej strefy — LAEA jest odwzorowaniem równopolowym, więc cała
    jego trygonometria idzie przez `q`, a nie przez szerokość geodezyjną."""
    es = e * sin_phi
    return (1 - e ** 2) * (sin_phi / (1 - es ** 2) - (1 / (2 * e)) * math.log((1 - es) / (1 + es)))


def _laea_constants():
    e = math.sqrt(F_GRS80 * (2 - F_GRS80))
    q_p = _laea_q(1.0, e)
    q_0 = _laea_q(math.sin(LAEA_LAT0), e)
    beta_0 = math.asin(q_0 / q_p)
    r_q = A_GRS80 * math.sqrt(q_p / 2.0)
    d = (A_GRS80 * math.cos(LAEA_LAT0) / math.sqrt(1 - e ** 2 * math.sin(LAEA_LAT0) ** 2)
         / (r_q * math.cos(beta_0)))
    return e, q_p, beta_0, r_q, d


def wgs84_to_laea3035(lon, lat):
    e, q_p, beta_0, r_q, d = _laea_constants()
    phi, lam = math.radians(lat), math.radians(lon)
    beta = math.asin(_laea_q(math.sin(phi), e) / q_p)
    dlam = lam - LAEA_LON0
    denominator = 1 + math.sin(beta_0) * math.sin(beta) + math.cos(beta_0) * math.cos(beta) * math.cos(dlam)
    b = r_q * math.sqrt(2.0 / denominator)
    east = LAEA_FE + b * d * math.cos(beta) * math.sin(dlam)
    north = LAEA_FN + (b / d) * (math.cos(beta_0) * math.sin(beta)
                                 - math.sin(beta_0) * math.cos(beta) * math.cos(dlam))
    return east, north


def _authalic_to_geodetic(beta, e, q_p, tolerance_rad=1e-14, iterations=8):
    """Odwrotność `q` przez Newtona zamiast szeregu Snydera.

    Szereg w e^6 zostawia ułamki milimetra, a iteracja schodzi do precyzji maszynowej
    w trzech krokach i jest krótsza do przeczytania niż cztery współczynniki.

    **Niezbieżność jest błędem, nie wynikiem** — ta sama konwencja i to samo
    brzmienie komunikatu, co w `lambert72_to_wgs84`. Krok Newtona dzieli przez
    `2*cos(phi)`, więc przy `beta` dążącym do ±90° iteracja przestaje się
    domykać: dla `beta = -90°` osiem kroków dawało wcześniej `phi = 270,355°`
    zwrócone bez żadnego sygnału.

    Kryterium jest **ostre**: `|step|` musi być *mniejsze* od `tolerance_rad`,
    czyli krok równy dokładnie progowi jest porażką. Zgadza się to z warunkiem
    przerwania pętli, którego ta zmiana nie rusza — domyślne `1e-14` rad i osiem
    iteracji są dokładnie te, co wcześniej, tylko dostały nazwy, żeby test mógł
    odczytać próg z wnętrza funkcji, a nie zgadywać go z zewnątrz.

    Zasięg, w którym osiem kroków nie domyka `1e-14` rad, zaczyna się przy
    |beta| ≈ 85,1°. Oś brukselska ma `beta` w [50,67°, 50,78°], czyli ponad 34°
    zapasu, a `laea3035_to_wgs84` liczy `beta` przez `asin`, więc nigdy nie
    wyjdzie poza ±90°.
    """
    q = q_p * math.sin(beta)
    phi = beta
    step = None
    for _ in range(iterations):
        sin_phi = math.sin(phi)
        es = e * sin_phi
        residual = (q / (1 - e ** 2) - sin_phi / (1 - es ** 2)
                    + (1 / (2 * e)) * math.log((1 - es) / (1 + es)))
        step = residual * (1 - es ** 2) ** 2 / (2 * math.cos(phi))
        phi += step
        if abs(step) < tolerance_rad:
            return phi
    raise ValueError(
        f"inwersja szerokości autalicznej rozbieżna dla beta {math.degrees(beta)} deg: "
        f"krok {abs(step)!r} rad nie zeszedł pod tolerancję {tolerance_rad!r} rad "
        f"po {iterations} iteracjach")


def laea3035_to_wgs84(east, north):
    e, q_p, beta_0, r_q, d = _laea_constants()
    x = (east - LAEA_FE) / d
    y = d * (north - LAEA_FN)
    rho = math.hypot(x, y)
    if rho < 1e-12:  # dokładnie w początku odwzorowania — kąt kierunkowy nieokreślony
        return math.degrees(LAEA_LON0), math.degrees(LAEA_LAT0)
    c = 2.0 * math.asin(rho / (2.0 * r_q))
    sin_c, cos_c = math.sin(c), math.cos(c)
    beta = math.asin(cos_c * math.sin(beta_0) + y * sin_c * math.cos(beta_0) / rho)
    lam = LAEA_LON0 + math.atan2(x * sin_c,
                                 rho * math.cos(beta_0) * cos_c - y * math.sin(beta_0) * sin_c)
    return math.degrees(lam), math.degrees(_authalic_to_geodetic(beta, e, q_p))


def laea3035_to_lambert72(east, north):
    """Skrót używany przez `tools/track/inspire_rail.py`: INSPIRE -> oś projektu.

    Osobna funkcja, a nie złożenie w miejscu wywołania, bo to złożenie niesie
    założenie ETRS89 ≈ WGS84 opisane wyżej i ma jedno miejsce, w którym da się je
    znaleźć i podważyć.
    """
    lon, lat = laea3035_to_wgs84(east, north)
    return wgs84_to_lambert72(lon, lat)
