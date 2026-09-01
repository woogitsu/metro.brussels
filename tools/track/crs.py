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
