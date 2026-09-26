#!/usr/bin/env python3
"""Bryły elementów stacji ponad peronem: schody, winda, antresola, korytarz, portal.

Trzeci etap T-211/T-212. Podział jest ten sam, co w całym paśmie geometrii i nie jest
kosmetyczny: **tu nie ma ani jednej linii `bpy`**, więc każdy wymiar i każde położenie
da się sprawdzić bez Blendera. `tools/blender/station_kit.py` bierze stąd listę brył
i zamienia je na siatki.

Wszystkie bryły są opisane jednolicie, jako **graniastosłup w ramce lokalnej osi**:

- `at_m` — kilometraż ramki, w której stoi bryła;
- `length_m` — rozciągłość WZDŁUŻ osi;
- `section` — wielokąt `(y, z)` w płaszczyźnie prostopadłej do osi, gdzie `y` idzie
  w prawo od kierunku jazdy, a `z` w górę od poziomu główki szyny.

Dzięki temu korytarz prostopadły do toru jest tym samym typem obiektu, co peron: ma
tylko krótką rozciągłość wzdłuż osi i długi wielokąt w `y`. Bryła `follows_axis`
jest zamiatana po łuku, `False` — prosta; różnica ma znaczenie tylko dla brył długich,
a te wszystkie idą wzdłuż osi.

## Czego tu nie ma i dlaczego

Układ antresoli, przebieg korytarzy i liczba wyjść **nie wynikają z żadnych danych**.
STIB nie publikuje rzutów stacji, a obrysy z UrbIS (R-007) mówią tylko, ile miejsca
stacja zajmuje na powierzchni. Ten moduł buduje więc układ **kanoniczny** — jeden
zespół schody + winda przy każdym końcu peronu, antresola nad komorą, jeden korytarz
i jeden portal na zespół — i mówi o tym wprost w `not_modelled`. To NIE jest rzut
żadnej brukselskiej stacji i nie wolno go tak przedstawiać.

Wszystkie wymiary poniżej są `design_assumption`. Żaden nie pochodzi ze STIB.
"""
import math

#: Wysokość stopnia. Wraz z `DESIGN_STAIR_GOING_M` daje wzór Blondela
#: `2 x podstopnica + stopnica = 0,63 m`, czyli środek pasma wygodnego dla ruchu pieszego.
DESIGN_STAIR_RISER_M = 0.17
#: Głębokość stopnia.
DESIGN_STAIR_GOING_M = 0.29
#: Szerokość biegu schodów.
DESIGN_STAIR_WIDTH_M = 2.40
#: Najwięcej stopni w jednym biegu; powyżej wchodzi spocznik.
DESIGN_STAIR_MAX_RISERS = 16
#: Długość spocznika między biegami.
DESIGN_STAIR_LANDING_M = 1.20
#: Rzut szybu windy: wzdłuż osi x w poprzek.
DESIGN_LIFT_PLAN_M = (2.10, 2.60)
#: Grubość płyty antresoli i płyty stropu komory.
DESIGN_SLAB_THICKNESS_M = 0.40
#: Wysokość w świetle na antresoli.
DESIGN_MEZZANINE_CLEAR_M = 2.60
#: Rozciągłość antresoli wzdłuż osi, liczona od końca peronu do środka.
DESIGN_MEZZANINE_LENGTH_M = 24.0
#: Korytarz z antresoli do portalu: szerokość, wysokość w świetle, długość.
DESIGN_CORRIDOR_WIDTH_M = 3.00
DESIGN_CORRIDOR_CLEAR_M = 2.40
DESIGN_CORRIDOR_LENGTH_M = 12.0
#: Portal wejściowy na końcu korytarza.
DESIGN_PORTAL_WIDTH_M = 4.00
DESIGN_PORTAL_CLEAR_M = 2.60
DESIGN_PORTAL_DEPTH_M = 1.50
#: Cienka projektowa powłoka przejścia. Daje 2,64 m w świetle w korytarzu
#: szerokości 3,00 m — więcej niż 2,40 m schodów; grubsza płyta 0,40 m
#: zwęziłaby przejście do 2,20 m. To założenie modelu, nie pomiar STIB.
DESIGN_ACCESS_SHELL_M = 0.18
#: Odsunięcie zespołu schody+winda od końca peronu, żeby nie stał na samej krawędzi.
DESIGN_ACCESS_SETBACK_M = 4.0
#: Zapas otworu w antresoli wokół obrysu schodów i windy — na balustradę i na to,
#: żeby krawędź płyty nie stała dokładnie na krawędzi stopnia.
DESIGN_VOID_MARGIN_M = 0.30
#: Długość peronu, na której stoi ten zespół — decyzja właściciela z 04.09.2026.
#:
#: R-007 §5 pkt 2 zostawia długość peronu jako `unknown` w danych i daje generatorowi
#: JAWNY parametr, bo żadne publiczne źródło jej nie podaje. Ta stała jest tym jawnym
#: parametrem dla T-212 i wynika z dwóch granic, które R-007 UDOWODNIŁ:
#:
#: - dolna: skład M7 ma 94,0 m (`data/vehicle/m7-spec.json`, status `spec`), a peron
#:   krótszy od składu jest sprzeczny z ruchem bez selektywnego otwierania drzwi;
#: - górna: obrys stacji z UrbIS, najciaśniej Parc 109,1 m (`TIGHTEST_STATION_FOOTPRINT_M`).
#:
#: 95,0 m = 94,0 m składu plus metr zapasu, po 0,50 m z każdej strony. Zapas nie jest
#: okrągły dla ozdoby: 1,00 m to 3,2× największy ZMIERZONY błąd zatrzymania autopilota
#: na pakiecie A (0,307 m, `reports/T-401-line-run.md` §2). Wartość mieści się też
#: w rozrzucie peronów OSM z R-007 §4 — 26 z 28 leży w 94,76 ± 0,78 m, czyli do 95,54 m.
DESIGN_PLATFORM_LENGTH_M = 95.0

#: NIE jest założeniem projektowym i dlatego stoi POZA `DESIGN_ASSUMPTIONS`: to POMIAR.
#: Rozciągłość obrysu stacji Parc rzutowana na kierunek osi, z poligonów `MS`
#: `urbis_metro_station_polygons` (CC0), R-007 §4 — najciaśniejszy obrys pakietu A.
#: R-007 §5 pkt 3 robi z niego kontrolę: „generator dający peron dłuższy niż obrys
#: stacji jest na pewno błędny".
TIGHTEST_STATION_FOOTPRINT_M = 109.1

DESIGN_ASSUMPTIONS = {
    "DESIGN_STAIR_RISER_M": DESIGN_STAIR_RISER_M,
    "DESIGN_STAIR_GOING_M": DESIGN_STAIR_GOING_M,
    "DESIGN_STAIR_WIDTH_M": DESIGN_STAIR_WIDTH_M,
    "DESIGN_STAIR_MAX_RISERS": DESIGN_STAIR_MAX_RISERS,
    "DESIGN_STAIR_LANDING_M": DESIGN_STAIR_LANDING_M,
    "DESIGN_LIFT_PLAN_M": list(DESIGN_LIFT_PLAN_M),
    "DESIGN_SLAB_THICKNESS_M": DESIGN_SLAB_THICKNESS_M,
    "DESIGN_MEZZANINE_CLEAR_M": DESIGN_MEZZANINE_CLEAR_M,
    "DESIGN_MEZZANINE_LENGTH_M": DESIGN_MEZZANINE_LENGTH_M,
    "DESIGN_CORRIDOR_WIDTH_M": DESIGN_CORRIDOR_WIDTH_M,
    "DESIGN_CORRIDOR_CLEAR_M": DESIGN_CORRIDOR_CLEAR_M,
    "DESIGN_CORRIDOR_LENGTH_M": DESIGN_CORRIDOR_LENGTH_M,
    "DESIGN_PORTAL_WIDTH_M": DESIGN_PORTAL_WIDTH_M,
    "DESIGN_PORTAL_CLEAR_M": DESIGN_PORTAL_CLEAR_M,
    "DESIGN_PORTAL_DEPTH_M": DESIGN_PORTAL_DEPTH_M,
    "DESIGN_ACCESS_SHELL_M": DESIGN_ACCESS_SHELL_M,
    "DESIGN_ACCESS_SETBACK_M": DESIGN_ACCESS_SETBACK_M,
    "DESIGN_VOID_MARGIN_M": DESIGN_VOID_MARGIN_M,
    "DESIGN_PLATFORM_LENGTH_M": DESIGN_PLATFORM_LENGTH_M,
}

COMPONENTS = ("stairs", "lift", "mezzanine", "corridor", "portal")

NOT_MODELLED = (
    "rzut stacji — STIB nie publikuje, UrbIS daje tylko obrys (R-007)",
    "liczba i położenie wyjść na powierzchnię",
    "bramki biletowe, kasy, przejścia między liniami",
    "konstrukcja: słupy, belki, dylatacje",
    "instalacje: wentylacja, odwodnienie, kable",
)


def platform_fits_the_station(length_m, footprint_m=TIGHTEST_STATION_FOOTPRINT_M):
    """Kontrola z R-007 §5 pkt 3: peron NIE MOŻE być dłuższy niż obrys stacji.

    To jedyna górna granica długości peronu, jaką da się udowodnić z danych — poligon
    stacji obejmuje peron, więc peron dłuższy od poligonu jest na pewno błędny. Granica
    NALEŻY do peronu: peron równy obrysowi jeszcze się w nim mieści, dopiero dłuższy
    wypada. Domyślnie brany jest najciaśniejszy przypadek pakietu A (Parc, 109,1 m), bo
    generator buduje jeden peron dla wszystkich dwunastu stacji i musi zmieścić się
    w najgorszej z nich, a nie w medianie.

    Kontrola jest tu, a nie w komentarzu, bo liczba w komentarzu nie jest wynikiem
    i nic jej nie porównuje. 110 m — pierwsza wartość tego zadania — wpada tu i wypada.
    """
    if length_m <= 0.0:
        raise ValueError(f"długość peronu musi być dodatnia, jest {length_m}")
    if footprint_m <= 0.0:
        raise ValueError(f"obrys stacji musi być dodatni, jest {footprint_m}")
    return length_m <= footprint_m + 1e-9


def rectangle(y_from, y_to, z_from, z_to):
    """Prostokąt `(y, z)` w kolejności przeciwnie do ruchu wskazówek dla `y` rosnącego."""
    if y_to <= y_from or z_to <= z_from:
        raise ValueError(f"prostokąt musi mieć dodatnie boki: y {y_from}..{y_to}, z {z_from}..{z_to}")
    return [(y_from, z_from), (y_to, z_from), (y_to, z_to), (y_from, z_to)]


def stair_flights(rise_m, riser_m=DESIGN_STAIR_RISER_M, going_m=DESIGN_STAIR_GOING_M,
                  max_risers=DESIGN_STAIR_MAX_RISERS, landing_m=DESIGN_STAIR_LANDING_M):
    """Podział wznoszenia na biegi i spoczniki.

    Zwraca listę odcinków `(rodzaj, liczba_stopni, dlugosc_m, z_od, z_do)`, gdzie rodzaj
    to `"flight"` albo `"landing"`. Liczba stopni jest **całkowita** i dobrana tak, żeby
    suma podstopnic dała dokładnie zadane wznoszenie — wysokość stopnia wychodzi więc
    nieco inna niż nominalna i to jest poprawne: schody muszą dojść tam, gdzie dochodzą,
    a nie tam, gdzie wypadnie z dzielenia.
    """
    if rise_m <= 0.0:
        raise ValueError("wznoszenie musi być dodatnie")
    total_risers = max(1, int(round(rise_m / riser_m)))
    actual_riser = rise_m / total_risers
    flights = max(1, math.ceil(total_risers / max_risers))
    per_flight = [total_risers // flights] * flights
    for index in range(total_risers - sum(per_flight)):
        per_flight[index] += 1

    out = []
    z = 0.0
    for index, risers in enumerate(per_flight):
        if index > 0:
            out.append(("landing", 0, landing_m, z, z))
        top = z + risers * actual_riser
        out.append(("flight", risers, risers * going_m, z, top))
        z = top
    return out


def stair_run_length_m(rise_m, **kwargs):
    """Rzut poziomy całego zespołu schodów — potrzebny, zanim postawi się cokolwiek obok."""
    return sum(length for _kind, _risers, length, _a, _b in stair_flights(rise_m, **kwargs))


def levels(platform_top_m, ceiling_m, slab_m=DESIGN_SLAB_THICKNESS_M,
           mezzanine_clear_m=DESIGN_MEZZANINE_CLEAR_M):
    """Poziomy stacji, liczone od poziomu główki szyny.

    Antresola idzie NAD stropem komory, nie wewnątrz niej, i to nie jest wybór estetyczny.
    Zmierzone na profilu `station`: strop stoi na 5,30 m, peron na 1,03 m, więc nad peronem
    zostaje 4,27 m. Antresola wewnątrz komory zabrałaby z tego płytę i dwa poziomy
    w świetle — dolny wyszedłby 2,40 m, a górny 1,47 m, czyli poniżej wzrostu człowieka.
    Komora zostaje więc jednokondygnacyjna, a antresola jest osobną skrzynią nad nią.
    """
    if ceiling_m <= platform_top_m:
        raise ValueError("strop komory musi być nad peronem")
    mezzanine_floor = ceiling_m + slab_m
    return {
        "platform_top_m": platform_top_m,
        "chamber_ceiling_m": ceiling_m,
        "chamber_clear_m": round(ceiling_m - platform_top_m, 6),
        "mezzanine_floor_m": round(mezzanine_floor, 6),
        "mezzanine_ceiling_m": round(mezzanine_floor + mezzanine_clear_m, 6),
        "stair_rise_m": round(mezzanine_floor - platform_top_m, 6),
    }


def _solid(name, kind, at_m, length_m, section, follows_axis=False):
    return {"name": name, "kind": kind, "at_m": round(at_m, 4),
            "length_m": round(length_m, 4), "section": [(round(y, 4), round(z, 4))
                                                        for y, z in section],
            "follows_axis": follows_axis}


def hollow_access_shell(name, kind, at_m, width_m, y_from, y_to, floor_m, clear_m,
                        thickness_m=DESIGN_ACCESS_SHELL_M):
    """Four prisms form an open passage instead of a solid obstacle.

    The axis span is the passage width. The cross section spans the passage
    length and height; the two jambs occupy only the outer strips of that
    axis span. Every solid keeps the component suffix for runtime styling.
    """
    if width_m <= 2 * thickness_m or clear_m <= 0 or y_to <= y_from:
        raise ValueError("access shell requires positive interior clearance")
    top_m = floor_m + clear_m
    return [
        _solid(f"{name}_floor_{kind}", kind, at_m, width_m,
               rectangle(y_from, y_to, floor_m - thickness_m, floor_m)),
        _solid(f"{name}_roof_{kind}", kind, at_m, width_m,
               rectangle(y_from, y_to, top_m, top_m + thickness_m)),
        _solid(f"{name}_jamb_a_{kind}", kind, at_m, thickness_m,
               rectangle(y_from, y_to, floor_m, top_m)),
        _solid(f"{name}_jamb_b_{kind}", kind,
               at_m + width_m - thickness_m, thickness_m,
               rectangle(y_from, y_to, floor_m, top_m)),
    ]


def mezzanine_slabs(name, at_m, length_m, y_from, y_to, floor_m, ceiling_m):
    """Keep the measured clear height open between separate floor and roof slabs."""
    return [
        _solid(name, "mezzanine", at_m, length_m,
               rectangle(y_from, y_to, floor_m - DESIGN_SLAB_THICKNESS_M, floor_m),
               follows_axis=True),
        _solid(f"{name}_roof", "mezzanine", at_m, length_m,
               rectangle(y_from, y_to, ceiling_m, ceiling_m + DESIGN_SLAB_THICKNESS_M),
               follows_axis=True),
    ]


def access_solids(platform, side, level, wall_m, prefix=""):
    """Zespół dostępu przy JEDNYM końcu peronu: schody, winda, antresola, korytarz, portal.

    `side` to +1 albo -1 — strona osi, po której stoi zespół. Zespół stoi przy końcu
    peronu o większym kilometrażu, odsunięty o `DESIGN_ACCESS_SETBACK_M`, i idzie
    w stronę malejącego kilometrażu, żeby nie wychodzić poza peron.
    """
    if side not in (1, -1, 1.0, -1.0):
        raise ValueError("strona musi być +1 albo -1")
    side = 1.0 if side > 0 else -1.0
    inner = side * (wall_m - DESIGN_CORRIDOR_WIDTH_M)
    outer = side * wall_m

    def span(a, b):
        return (min(a, b), max(a, b))

    solids = []
    run_m = stair_run_length_m(level["stair_rise_m"])
    top_m = platform["to_m"] - DESIGN_ACCESS_SETBACK_M
    cursor = top_m - run_m

    half = DESIGN_STAIR_WIDTH_M / 2.0
    centre = side * (wall_m - DESIGN_STAIR_WIDTH_M / 2.0 - 0.20)
    y_from, y_to = span(centre - half, centre + half)
    for index, (kind, risers, length_m, z_from, z_to) in enumerate(
            stair_flights(level["stair_rise_m"])):
        base = level["platform_top_m"]
        if kind == "landing":
            solids.append(_solid(
                f"{prefix}stairs{index}_landing", "stairs", cursor, length_m,
                rectangle(y_from, y_to, base + z_from - 0.20, base + z_from)))
        else:
            step_len = length_m / risers
            for step in range(risers):
                z_top = base + z_from + (z_to - z_from) * (step + 1) / risers
                solids.append(_solid(
                    f"{prefix}stairs{index}_{step:02d}", "stairs",
                    cursor + step * step_len, step_len,
                    rectangle(y_from, y_to, base, z_top)))
        cursor += length_m

    lift_len, lift_width = DESIGN_LIFT_PLAN_M
    lift_centre = side * (wall_m - DESIGN_STAIR_WIDTH_M - lift_width / 2.0 - 0.60)
    ly_from, ly_to = span(lift_centre - lift_width / 2.0, lift_centre + lift_width / 2.0)
    solids.append(_solid(
        f"{prefix}lift", "lift", top_m - lift_len, lift_len,
        rectangle(ly_from, ly_to, level["platform_top_m"], level["mezzanine_ceiling_m"])))

    # Antresola z OTWOREM, a nie zamknięta płyta. Otwór nie jest wymyślony: wynika
    # z obrysu tego, co ma przez niego przechodzić — schodów i szybu windy. Pierwsza
    # wersja budowała jedną płytę na całą szerokość i render `_side` pokazał to
    # natychmiast: schody dobijały do jej spodu i kończyły się sufitem.
    #
    # Płyta jest cięta na trzy odcinki wzdłuż osi — przed otworem, przy otworze
    # i za nim — a przy otworze zostają dwa pasy po bokach. Cztery graniastosłupy
    # zamiast jednego, zero operacji boolowskich.
    mez_from = top_m - DESIGN_MEZZANINE_LENGTH_M
    my_from, my_to = span(-wall_m, wall_m)
    floor_z, ceiling_z = level["mezzanine_floor_m"], level["mezzanine_ceiling_m"]

    through = [s for s in solids if s["kind"] in ("stairs", "lift")]
    void_from = min(s["at_m"] for s in through)
    void_to = max(s["at_m"] + s["length_m"] for s in through)
    void_from = max(void_from, mez_from)
    void_ys = [y for s in through for y, _z in s["section"]]
    void_y_from = max(my_from, min(void_ys) - DESIGN_VOID_MARGIN_M)
    void_y_to = min(my_to, max(void_ys) + DESIGN_VOID_MARGIN_M)

    if void_from - mez_from > 1e-6:
        solids.extend(mezzanine_slabs(
            f"{prefix}mezzanine_a", mez_from, void_from - mez_from,
            my_from, my_to, floor_z, ceiling_z))
    # Pasy przy otworze nazywane ROLĄ, nie stroną osi. Pierwsza wersja nazywała je
    # `l` i `r` po algebraicznym znaku `y` — i wtedy odbicie lustrzane zespołu
    # przestawało być odbiciem, bo pas „lewy" po jednej stronie odpowiadał „prawemu"
    # po drugiej. Test lustra wywrócił się na tym od razu.
    for y_a, y_b in ((my_from, void_y_from), (void_y_to, my_to)):
        if y_b - y_a <= 1e-6:
            continue
        near = y_a <= side * wall_m <= y_b
        solids.extend(mezzanine_slabs(
            f"{prefix}mezzanine_{'near' if near else 'far'}",
            void_from, void_to - void_from,
            y_a, y_b, floor_z, ceiling_z))
    if top_m - void_to > 1e-6:
        solids.extend(mezzanine_slabs(
            f"{prefix}mezzanine_b", void_to, top_m - void_to,
            my_from, my_to, floor_z, ceiling_z))

    corridor_far = side * (wall_m + DESIGN_CORRIDOR_LENGTH_M)
    cy_from, cy_to = span(outer, corridor_far)
    corridor_at = top_m - DESIGN_MEZZANINE_LENGTH_M / 2.0 - DESIGN_CORRIDOR_WIDTH_M / 2.0
    solids.extend(hollow_access_shell(
        f"{prefix}corridor", "corridor", corridor_at, DESIGN_CORRIDOR_WIDTH_M,
        cy_from, cy_to, level["mezzanine_floor_m"], DESIGN_CORRIDOR_CLEAR_M))

    portal_far = side * (wall_m + DESIGN_CORRIDOR_LENGTH_M + DESIGN_PORTAL_DEPTH_M)
    py_from, py_to = span(corridor_far, portal_far)
    solids.extend(hollow_access_shell(
        f"{prefix}portal", "portal",
        top_m - DESIGN_MEZZANINE_LENGTH_M / 2.0 - DESIGN_PORTAL_WIDTH_M / 2.0,
        DESIGN_PORTAL_WIDTH_M, py_from, py_to,
        level["mezzanine_floor_m"], DESIGN_PORTAL_CLEAR_M))

    _ = inner
    return solids


def station_solids(platform, level, wall_m, components=COMPONENTS, side=1):
    """Wszystkie zamówione bryły dostępu dla jednego peronu."""
    unknown = [c for c in components if c not in COMPONENTS]
    if unknown:
        raise ValueError(f"nieznane elementy: {unknown}; znane: {list(COMPONENTS)}")
    wanted = set(components)
    return [s for s in access_solids(platform, side, level, wall_m)
            if s["kind"] in wanted]
