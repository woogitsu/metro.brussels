#!/usr/bin/env python3
"""Układ KANONICZNY kabiny maszynisty — czysty Python, bez `bpy`.

Ten sam podział, co w `tools/track/station_components.py`, i ten sam powód: **nie ma
tu ani jednej linii `bpy`**, więc każdy wymiar i każde położenie da się sprawdzić bez
Blendera. `tools/blender/m7_cab_build.py` bierze stąd listę brył i zamienia je na
siatki.

## Czego tu nie ma i dlaczego

**To nie jest kabina M7.** STIB nie publikuje rzutów kabiny, a `docs/03-legal.md` nie
daje prawa do cudzych rysunków ani do odwzorowywania jej ze zdjęć. Ten moduł buduje
układ **kanoniczny** — podłoga, ściana do przedziału pasażerskiego z jednymi drzwiami,
pulpit i fotel — i mówi o tym wprost w `NOT_MODELLED`, tak samo jak zespół dostępu
stacji mówi to o antresoli. Żadnej z tych liczb nie wolno przedstawiać jako wymiaru
pojazdu M7.

Ze `spec` przychodzą **wyłącznie** wymiary skorupy, przez `m7_layout.Layout`: szerokość
pudła, wysokość podłogi i długość składu. Wszystko poniżej jest `design_assumption`
i ma wpis w `docs/21-measured-vs-assumed.md`.

## Kształt danych

Bryła jest **prostopadłościanem w ramce pojazdu**: `(x_from_m, x_to_m, y_from_m,
y_to_m, z_from_m, z_to_m)`. Pudełko, a nie graniastosłup z wielokątem przekroju jak
w `station_components`, i to jest wybór: kabina nie jedzie po łuku i nie jest
zamiatana wzdłuż osi, więc wielokąt kupowałby wyłącznie możliwość pomyłki. Osiem
wierzchołków i sześć ścian da się przeczytać w całości.

Osie wg `docs/04-conventions.md`: X wzdłuż składu (0 = czoło pierwszej kabiny),
Y w poprzek (0 = oś toru), Z w górę (0 = główka szyny). 1 jednostka = 1 metr.
"""
import m7_layout

#: Odległość od czubka czoła do wewnętrznego lica szyby czołowej. Kabina zaczyna się
#: ZA nosem, bo nos jest ścięciem skorupy, nie przestrzenią do stania.
DESIGN_CAB_BULKHEAD_FRONT_M = 0.35
#: Grubość wykładziny na ścianie bocznej, mierzona od lica skorupy do wnętrza.
#: Bez niej podłoga sięgałaby dokładnie do blachy i każdy błąd zaokrąglenia wychodziłby
#: poza pudło.
DESIGN_CAB_LINING_M = 0.05
#: Grubość płyty podłogowej kabiny; podłoga leży NA wysokości podłogi pudła ze `spec`.
DESIGN_CAB_FLOOR_SLAB_M = 0.06
#: Światło kabiny nad podłogą.
DESIGN_CAB_CLEAR_HEIGHT_M = 2.05
#: Grubość ściany do przedziału pasażerskiego.
DESIGN_CAB_BULKHEAD_M = 0.08
#: Drzwi w ścianie do przedziału pasażerskiego: szerokość i wysokość światła.
DESIGN_BULKHEAD_DOOR_WIDTH_M = 0.70
DESIGN_BULKHEAD_DOOR_HEIGHT_M = 1.90
#: Pulpit: blat, jego grubość i wysokość górnego lica nad podłogą kabiny.
DESIGN_DESK_WIDTH_M = 1.40
DESIGN_DESK_DEPTH_M = 0.60
DESIGN_DESK_TOP_M = 0.95
DESIGN_DESK_SLAB_M = 0.10
#: Odstęp między licem szyby czołowej a przednią krawędzią pulpitu.
DESIGN_DESK_FRONT_GAP_M = 0.15
#: Fotel: siedzisko i oparcie. Siedzisko jest bryłą, nie kształtem — ta pozycja robi
#: bryłę, nie wyposażenie.
DESIGN_SEAT_WIDTH_M = 0.50
DESIGN_SEAT_DEPTH_M = 0.45
DESIGN_SEAT_CUSHION_M = 0.48
DESIGN_SEAT_BACK_HEIGHT_M = 0.55
DESIGN_SEAT_BACK_M = 0.10
#: Odstęp między tylną krawędzią pulpitu a przednią krawędzią siedziska.
DESIGN_SEAT_GAP_FROM_DESK_M = 0.35
#: Szyba czołowa: parapet i nadproże nad podłogą kabiny oraz margines od ściany bocznej.
DESIGN_WINDSCREEN_SILL_M = 0.95
DESIGN_WINDSCREEN_HEAD_M = 1.95
DESIGN_WINDSCREEN_MARGIN_M = 0.15
#: Okno boczne kabiny: długość wzdłuż osi, parapet i nadproże nad podłogą kabiny.
DESIGN_CAB_WINDOW_LENGTH_M = 0.70
DESIGN_CAB_WINDOW_SILL_M = 1.00
DESIGN_CAB_WINDOW_HEAD_M = 1.60

DESIGN_ASSUMPTIONS = {
    "cab_bulkhead_front_m": (DESIGN_CAB_BULKHEAD_FRONT_M,
                             "odległość czubka czoła od lica szyby czołowej"),
    "cab_lining_m": (DESIGN_CAB_LINING_M, "grubość wykładziny ściany bocznej"),
    "cab_floor_slab_m": (DESIGN_CAB_FLOOR_SLAB_M, "grubość płyty podłogowej kabiny"),
    "cab_clear_height_m": (DESIGN_CAB_CLEAR_HEIGHT_M, "światło kabiny nad podłogą"),
    "cab_bulkhead_m": (DESIGN_CAB_BULKHEAD_M, "grubość ściany do przedziału pasażerskiego"),
    "bulkhead_door_width_m": (DESIGN_BULKHEAD_DOOR_WIDTH_M, "szerokość drzwi w ścianie kabiny"),
    "bulkhead_door_height_m": (DESIGN_BULKHEAD_DOOR_HEIGHT_M, "wysokość światła tych drzwi"),
    "desk_width_m": (DESIGN_DESK_WIDTH_M, "szerokość pulpitu"),
    "desk_depth_m": (DESIGN_DESK_DEPTH_M, "głębokość pulpitu wzdłuż osi"),
    "desk_top_m": (DESIGN_DESK_TOP_M, "wysokość górnego lica pulpitu nad podłogą kabiny"),
    "desk_slab_m": (DESIGN_DESK_SLAB_M, "grubość blatu pulpitu"),
    "desk_front_gap_m": (DESIGN_DESK_FRONT_GAP_M, "odstęp szyby czołowej od pulpitu"),
    "seat_width_m": (DESIGN_SEAT_WIDTH_M, "szerokość siedziska"),
    "seat_depth_m": (DESIGN_SEAT_DEPTH_M, "głębokość siedziska"),
    "seat_cushion_m": (DESIGN_SEAT_CUSHION_M, "wysokość górnego lica siedziska nad podłogą"),
    "seat_back_height_m": (DESIGN_SEAT_BACK_HEIGHT_M, "wysokość oparcia nad siedziskiem"),
    "seat_back_m": (DESIGN_SEAT_BACK_M, "grubość oparcia"),
    "seat_gap_from_desk_m": (DESIGN_SEAT_GAP_FROM_DESK_M, "odstęp pulpitu od siedziska"),
    "windscreen_sill_m": (DESIGN_WINDSCREEN_SILL_M, "parapet szyby czołowej nad podłogą kabiny"),
    "windscreen_head_m": (DESIGN_WINDSCREEN_HEAD_M, "nadproże szyby czołowej"),
    "windscreen_margin_m": (DESIGN_WINDSCREEN_MARGIN_M, "margines szyby czołowej od ściany bocznej"),
    "cab_window_length_m": (DESIGN_CAB_WINDOW_LENGTH_M, "długość okna bocznego kabiny"),
    "cab_window_sill_m": (DESIGN_CAB_WINDOW_SILL_M, "parapet okna bocznego"),
    "cab_window_head_m": (DESIGN_CAB_WINDOW_HEAD_M, "nadproże okna bocznego"),
}

#: Czego ten układ NIE odwzorowuje. Wypisane tak samo jawnie, jak wymiary — zdanie
#: „to nie jest kabina M7" ma jechać razem z geometrią, a nie zostać w raporcie.
NOT_MODELLED = (
    "rozkład pulpitu i rozmieszczenie nastawników — STIB nie publikuje rzutów kabiny",
    "kształt fotela maszynisty; tu jest bryła siedziska i oparcia, nie mebel",
    "przyrządy, wskaźniki i cokolwiek pokazującego stan pociągu",
    "rzeczywiste wymiary kabiny M7 — wszystkie liczby są design_assumption",
)


#: Wierzchołki pudełka, w kolejności, której używa `FACES`. Spód (z_from) najpierw,
#: obchodzony przeciwnie do ruchu wskazówek patrząc Z GÓRY, potem góra tak samo.
def verts(box):
    x0, x1 = box["x_from_m"], box["x_to_m"]
    y0, y1 = box["y_from_m"], box["y_to_m"]
    z0, z1 = box["z_from_m"], box["z_to_m"]
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]


#: Sześć ścian pudełka po indeksach z `verts`. Kolejność w każdej ścianie jest taka,
#: żeby normalna WYCHODZIŁA NA ZEWNĄTRZ bryły.
#:
#: **Ta tabela stoi tutaj, a nie w generatorze, i to jest cała różnica.** Pierwsza
#: wersja miała ją w module z `bpy`, więc jedynym sposobem sprawdzenia windingu był
#: render — i pierwsza wersja windingu była ZŁA: klatka `_normals` dała
#: `tylna_strona=0.65`, czyli dwie trzecie widocznej powierzchni od podszewki.
#: Tabela w module bez `bpy` daje się sprawdzić iloczynem wektorowym, bez Blendera,
#: i tak jest sprawdzana w `tools/tests/test_m7_cab.py`.
FACES = (
    (0, 3, 2, 1),  # spód,   normalna -Z
    (4, 5, 6, 7),  # góra,   normalna +Z
    (0, 1, 5, 4),  # y_from, normalna -Y
    (3, 7, 6, 2),  # y_to,   normalna +Y
    (0, 4, 7, 3),  # x_from, normalna -X
    (1, 2, 6, 5),  # x_to,   normalna +X
)


def face_normal(punkty):
    """Normalna ściany z trzech pierwszych wierzchołków, znormalizowana do znaku."""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = punkty[:3]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - bx, cy - by, cz - bz
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)


def _box(name, kind, x_from, x_to, y_from, y_to, z_from, z_to):
    if not (x_from < x_to and y_from < y_to and z_from < z_to):
        raise ValueError(f"{name}: pudełko o niedodatniej krawędzi "
                         f"({x_from}, {x_to}, {y_from}, {y_to}, {z_from}, {z_to})")
    return {"name": name, "kind": kind,
            "x_from_m": round(x_from, 4), "x_to_m": round(x_to, 4),
            "y_from_m": round(y_from, 4), "y_to_m": round(y_to, 4),
            "z_from_m": round(z_from, 4), "z_to_m": round(z_to, 4)}


class Cab:
    """Kabina przy JEDNYM końcu składu, w ramce pojazdu.

    `end` to `0` (czoło, X rośnie w głąb kabiny) albo `1` (tył, X maleje). Druga
    kabina jest lustrem pierwszej względem środka składu — tak samo, jak traktuje
    obie `m7_layout.Layout.cab_doors_list`.
    """

    def __init__(self, layout=None, end=0):
        self.layout = layout or m7_layout.Layout()
        if end not in (0, 1):
            raise ValueError(f"koniec składu to 0 albo 1, nie {end}")
        self.end = end
        self.cab_length = m7_layout.DESIGN_CAB_LENGTH_M
        self.floor_z = self.layout.floor_z
        self.ceiling_z = self.floor_z + DESIGN_CAB_FLOOR_SLAB_M + DESIGN_CAB_CLEAR_HEIGHT_M
        #: Połowa szerokości wnętrza liczona w NAJWĘŻSZYM miejscu kabiny, czyli przy
        #: licu szyby czołowej. Dzięki temu każda bryła mieści się w skorupie na całej
        #: swojej długości, bez liczenia zwężenia dla każdej z osobna — a że skorupa
        #: zwęża się ku czołu, węższy jest zawsze przód.
        inset, _drop = self.layout.taper(DESIGN_CAB_BULKHEAD_FRONT_M)
        self.half_width = self.layout.half_width - inset - DESIGN_CAB_LINING_M

    # --- ramka wzdłużna -------------------------------------------------------

    def x(self, distance_from_end):
        """X w ramce pojazdu dla odległości mierzonej od czoła TEJ kabiny."""
        if self.end == 0:
            return distance_from_end
        return self.layout.length - distance_from_end

    def span(self, near, far):
        """Para `(x_from, x_to)` posortowana rosnąco, z odległości od czoła kabiny."""
        a, b = self.x(near), self.x(far)
        return (a, b) if a < b else (b, a)

    # --- bryły ----------------------------------------------------------------

    def solids(self):
        """Wszystkie bryły kabiny: podłoga, ściana z drzwiami, pulpit, fotel."""
        przedrostek = "cab_front" if self.end == 0 else "cab_rear"
        floor_top = self.floor_z + DESIGN_CAB_FLOOR_SLAB_M
        wnetrze_od = DESIGN_CAB_BULKHEAD_FRONT_M
        wnetrze_do = self.cab_length - DESIGN_CAB_BULKHEAD_M
        out = []

        x0, x1 = self.span(wnetrze_od, self.cab_length)
        out.append(_box(f"{przedrostek}_floor", "floor", x0, x1,
                        -self.half_width, self.half_width, self.floor_z, floor_top))

        # Ściana do przedziału pasażerskiego: dwa słupki i nadproże wokół otworu.
        x0, x1 = self.span(wnetrze_do, self.cab_length)
        polowa_drzwi = DESIGN_BULKHEAD_DOOR_WIDTH_M / 2.0
        nadproze = floor_top + DESIGN_BULKHEAD_DOOR_HEIGHT_M
        out.append(_box(f"{przedrostek}_bulkhead_left", "wall", x0, x1,
                        -self.half_width, -polowa_drzwi, floor_top, self.ceiling_z))
        out.append(_box(f"{przedrostek}_bulkhead_right", "wall", x0, x1,
                        polowa_drzwi, self.half_width, floor_top, self.ceiling_z))
        out.append(_box(f"{przedrostek}_bulkhead_head", "wall", x0, x1,
                        -polowa_drzwi, polowa_drzwi, nadproze, self.ceiling_z))

        # Pulpit: bryła konsoli i blat nad nią.
        desk_near = wnetrze_od + DESIGN_DESK_FRONT_GAP_M
        desk_far = desk_near + DESIGN_DESK_DEPTH_M
        polowa_pulpitu = DESIGN_DESK_WIDTH_M / 2.0
        blat_od = floor_top + DESIGN_DESK_TOP_M - DESIGN_DESK_SLAB_M
        x0, x1 = self.span(desk_near, desk_far)
        out.append(_box(f"{przedrostek}_desk_body", "fitting", x0, x1,
                        -polowa_pulpitu, polowa_pulpitu, floor_top, blat_od))
        out.append(_box(f"{przedrostek}_desk_top", "fitting", x0, x1,
                        -polowa_pulpitu, polowa_pulpitu, blat_od,
                        floor_top + DESIGN_DESK_TOP_M))

        # Fotel: siedzisko i oparcie za nim.
        seat_near = desk_far + DESIGN_SEAT_GAP_FROM_DESK_M
        seat_far = seat_near + DESIGN_SEAT_DEPTH_M
        polowa_fotela = DESIGN_SEAT_WIDTH_M / 2.0
        x0, x1 = self.span(seat_near, seat_far)
        out.append(_box(f"{przedrostek}_seat_cushion", "fitting", x0, x1,
                        -polowa_fotela, polowa_fotela, floor_top,
                        floor_top + DESIGN_SEAT_CUSHION_M))
        x0, x1 = self.span(seat_far, seat_far + DESIGN_SEAT_BACK_M)
        out.append(_box(f"{przedrostek}_seat_back", "fitting", x0, x1,
                        -polowa_fotela, polowa_fotela,
                        floor_top + DESIGN_SEAT_CUSHION_M,
                        floor_top + DESIGN_SEAT_CUSHION_M + DESIGN_SEAT_BACK_HEIGHT_M))
        return out

    # --- otwory ---------------------------------------------------------------

    def openings(self):
        """Szyba czołowa i dwa okna boczne jako prostokąty — DANE, nie geometria.

        Wycięcie otworu w skorupie należy do generatora skorupy (`m7_shell.py`),
        którego ta pozycja nie zmienia. Tutaj otwory są policzone i sprawdzone, żeby
        ich wymiary miały wpis w audycie i żeby dało się pokazać, że mieszczą się
        w przekroju pudła — a nie żeby udawać, że kabina ma szyby.
        """
        floor_top = self.floor_z + DESIGN_CAB_FLOOR_SLAB_M
        polowa_szyby = self.half_width - DESIGN_WINDSCREEN_MARGIN_M
        out = [{
            "name": ("cab_front" if self.end == 0 else "cab_rear") + "_windscreen",
            "kind": "windscreen",
            "at_x_m": round(self.x(DESIGN_CAB_BULKHEAD_FRONT_M), 4),
            "y_from_m": round(-polowa_szyby, 4), "y_to_m": round(polowa_szyby, 4),
            "z_from_m": round(floor_top + DESIGN_WINDSCREEN_SILL_M, 4),
            "z_to_m": round(floor_top + DESIGN_WINDSCREEN_HEAD_M, 4),
        }]
        srodek = DESIGN_CAB_BULKHEAD_FRONT_M + DESIGN_DESK_FRONT_GAP_M \
            + DESIGN_DESK_DEPTH_M + DESIGN_SEAT_GAP_FROM_DESK_M
        x0, x1 = self.span(srodek, srodek + DESIGN_CAB_WINDOW_LENGTH_M)
        for side in (1, -1):
            out.append({
                "name": ("cab_front" if self.end == 0 else "cab_rear")
                        + ("_window_right" if side == 1 else "_window_left"),
                "kind": "cab_window",
                "side": side,
                "x_from_m": round(x0, 4), "x_to_m": round(x1, 4),
                "z_from_m": round(floor_top + DESIGN_CAB_WINDOW_SILL_M, 4),
                "z_to_m": round(floor_top + DESIGN_CAB_WINDOW_HEAD_M, 4),
            })
        return out


def both_cabs(layout=None):
    """Bryły obu kabin składu, w kolejności: czoło, tył."""
    layout = layout or m7_layout.Layout()
    return [Cab(layout, end=0), Cab(layout, end=1)]


def report(layout=None):
    """Słownik do zapisania obok `.glb` — wymiary, bryły, otwory i `NOT_MODELLED`."""
    layout = layout or m7_layout.Layout()
    kabiny = both_cabs(layout)
    return {
        "kind": "m7_cab_canonical",
        "not_modelled": list(NOT_MODELLED),
        "design_assumptions": {k: v[0] for k, v in DESIGN_ASSUMPTIONS.items()},
        "cab_length_m": m7_layout.DESIGN_CAB_LENGTH_M,
        "interior_half_width_m": round(kabiny[0].half_width, 4),
        "floor_top_m": round(kabiny[0].floor_z + DESIGN_CAB_FLOOR_SLAB_M, 4),
        "ceiling_m": round(kabiny[0].ceiling_z, 4),
        "solids": [s for cab in kabiny for s in cab.solids()],
        "openings": [o for cab in kabiny for o in cab.openings()],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(report(), ensure_ascii=False, indent=1))
