"""Rozkład wzdłużny i przekrój bryły M7 — czysty Python, bez bpy.

Wymiary `spec` pochodzą **wyłącznie** z `data/vehicle/m7-spec.json` (ground truth
T-904, źródło pierwotne STIB 13.07.2020). Nic tu nie jest przepisywane z Wikipedii,
zdjęć, Sketchfaba ani modeli fanowskich.

Wszystko, czego nie ma w rejestrze, jest jawnym `design_assumption`: stałą
`DESIGN_*` z komentarzem, dlaczego taka wartość. Żadna z nich nie awansuje do
`spec` bez źródła pierwotnego w T-904 (#8).

Osie wg `docs/04-conventions.md`: X wzdłuż składu (0 = czoło pierwszej kabiny),
Y w poprzek (0 = oś toru), Z w górę (0 = główka szyny). 1 jednostka = 1 metr.
"""
import json
import math
import os

import profiles

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SPEC_PATH = os.path.join(ROOT, "data", "vehicle", "m7-spec.json")

# --- design_assumption: wymiary bez źródła pierwotnego -------------------------
# Wysokość całkowita i faza dachu są już w repo jako wartości projektowe skrajni
# (tools/blender/profiles.py). Reużywamy ich, żeby bryła i profile tuneli nie
# rozjechały się na dwie różne "prawdy".
DESIGN_TOTAL_HEIGHT_M = profiles.M7_HEIGHT_M
DESIGN_ROOF_CHAMFER_M = profiles.M7_ROOF_CHAMFER_M
# Grubość ścianki skorupy — potrzebna, by otwór drzwiowy był otworem, a nie wnęką.
# Spód pudła leży dokładnie o tę grubość poniżej podłogi, dzięki czemu wewnętrzne
# lico płyty podłogowej wypada dokładnie na source-backed 1,03 m.
DESIGN_SHELL_THICKNESS_M = 0.08
# Neutralna strefa okienna wewnątrz istniejącej ściany, nie dodatkowa bryła ani
# odwzorowanie konkretnego wzoru M7. Otwory drzwiowe przecinają ją naturalnie.
DESIGN_WINDOW_BAND_BOTTOM_M = 2.05
DESIGN_WINDOW_BAND_TOP_M = 2.78
# Przegub między członami: długość przewężenia i wcięcie na stronę.
DESIGN_ARTICULATION_LENGTH_M = 1.10
DESIGN_ARTICULATION_INSET_M = 0.18
# Czoło: proste ścięcie liniowe. Bez zgadywania promieni czoła ze zdjęć.
DESIGN_NOSE_LENGTH_M = 2.40
DESIGN_NOSE_INSET_M = 0.45
DESIGN_NOSE_ROOF_DROP_M = 0.30
# Strefa kabiny: brak drzwi pasażerskich.
DESIGN_CAB_LENGTH_M = 3.60
# Otwory: wysokość światła i szerokość drzwi kabinowych.
DESIGN_DOOR_OPENING_HEIGHT_M = 1.95
DESIGN_CAB_DOOR_WIDTH_M = 0.80
DESIGN_CAB_DOOR_HEIGHT_M = 1.87
DESIGN_CAB_DOOR_CENTER_FROM_END_M = 2.90
# Podział długości między człony: równy. Brak źródła na rzeczywisty podział.
DESIGN_EQUAL_CAR_SPLIT = True

DESIGN_ASSUMPTIONS = {
    "total_height_m": (DESIGN_TOTAL_HEIGHT_M, "wysokość całkowita; wartość projektowa skrajni z tools/blender/profiles.py"),
    "roof_chamfer_m": (DESIGN_ROOF_CHAMFER_M, "faza dachu; wartość projektowa skrajni z tools/blender/profiles.py"),
    "shell_thickness_m": (DESIGN_SHELL_THICKNESS_M,
                          "grubość skorupy; bez niej otwór drzwiowy byłby wnęką, a spód pudła "
                          "leży o nią niżej, żeby lico podłogi wypadło dokładnie na 1,03 m"),
    "window_band_bottom_m": (DESIGN_WINDOW_BAND_BOTTOM_M,
                             "dolna krawędź neutralnego pasa okiennego na bocznej ścianie"),
    "window_band_top_m": (DESIGN_WINDOW_BAND_TOP_M,
                          "górna krawędź neutralnego pasa okiennego poniżej fazy dachu"),
    "articulation_length_m": (DESIGN_ARTICULATION_LENGTH_M, "długość przewężenia przegubowego między członami"),
    "articulation_inset_m": (DESIGN_ARTICULATION_INSET_M, "wcięcie przegubu na stronę"),
    "nose_length_m": (DESIGN_NOSE_LENGTH_M, "długość ścięcia czoła; ścięcie liniowe zamiast zgadywanych promieni"),
    "nose_inset_m": (DESIGN_NOSE_INSET_M, "zwężenie czoła na stronę na końcu ścięcia"),
    "nose_roof_drop_m": (DESIGN_NOSE_ROOF_DROP_M, "obniżenie dachu na końcu ścięcia czoła"),
    "cab_length_m": (DESIGN_CAB_LENGTH_M, "strefa kabiny bez drzwi pasażerskich"),
    "door_opening_height_m": (DESIGN_DOOR_OPENING_HEIGHT_M, "wysokość światła drzwi podwójnych"),
    "cab_door_width_m": (DESIGN_CAB_DOOR_WIDTH_M, "szerokość drzwi kabinowych; spec podaje tylko ich liczbę"),
    "cab_door_height_m": (DESIGN_CAB_DOOR_HEIGHT_M, "wysokość światła drzwi kabinowych"),
    "cab_door_center_from_end_m": (DESIGN_CAB_DOOR_CENTER_FROM_END_M, "położenie drzwi kabinowych za ścięciem czoła"),
    "equal_car_split": (DESIGN_EQUAL_CAR_SPLIT, "równy podział 94 m na 6 członów; brak źródła na rzeczywisty podział"),
}


def load_spec(path=SPEC_PATH):
    """Wyciąga z canonical registry wyłącznie pola o statusie `spec`."""
    with open(path, encoding="utf-8") as handle:
        registry = json.load(handle)
    parameters = registry["parameters"]
    needed = ("cars", "length_m", "width_m", "floor_height_m", "double_doors_per_side",
              "single_cab_doors_total", "double_door_opening_width_m")
    spec = {}
    for name in needed:
        record = parameters[name]
        if record["status"] != "spec":
            raise ValueError(f"{name} nie ma statusu spec — nie wolno go użyć jako wymiaru bryły")
        spec[name] = record["value"]
    spec["source_id"] = parameters["length_m"]["source_id"]
    spec["source_url"] = registry["sources"][spec["source_id"]]["url"]
    return spec


class Layout:
    """Rozkład wzdłużny składu wyliczony ze spec + jawnych design_assumption."""

    def __init__(self, spec=None):
        self.spec = spec or load_spec()
        self.length = float(self.spec["length_m"])
        self.width = float(self.spec["width_m"])
        self.half_width = self.width / 2.0
        self.floor_z = float(self.spec["floor_height_m"])
        self.cars = int(self.spec["cars"])
        self.doors_per_side = int(self.spec["double_doors_per_side"])
        self.cab_doors = int(self.spec["single_cab_doors_total"])
        self.door_width = float(self.spec["double_door_opening_width_m"])

        self.body_bottom_z = self.floor_z - DESIGN_SHELL_THICKNESS_M
        self.roof_z = DESIGN_TOTAL_HEIGHT_M
        self.car_length = self.length / self.cars
        if self.doors_per_side % self.cars:
            raise ValueError(f"{self.doors_per_side} drzwi nie dzieli się równo na {self.cars} członów")
        self.doors_per_car = self.doors_per_side // self.cars

    # --- podział wzdłużny -----------------------------------------------------

    def car_bounds(self, index):
        """Nominalne granice członu (bez skrócenia o przegub)."""
        return index * self.car_length, (index + 1) * self.car_length

    def car_body_span(self, index):
        """Fizyczny zakres X pudła członu — skrócony o połowę przegubu na wewnętrznych końcach."""
        start, end = self.car_bounds(index)
        half_joint = DESIGN_ARTICULATION_LENGTH_M / 2.0
        if index > 0:
            start += half_joint
        if index < self.cars - 1:
            end -= half_joint
        return start, end

    def articulation_spans(self):
        half_joint = DESIGN_ARTICULATION_LENGTH_M / 2.0
        return [(self.car_bounds(i)[1] - half_joint, self.car_bounds(i)[1] + half_joint)
                for i in range(self.cars - 1)]

    def door_usable_span(self, index):
        """Zakres X, w którym mogą stać drzwi pasażerskie tego członu."""
        start, end = self.car_body_span(index)
        if index == 0:
            start = DESIGN_CAB_LENGTH_M
        if index == self.cars - 1:
            end = self.length - DESIGN_CAB_LENGTH_M
        return start, end

    def double_doors(self):
        """Lista otworów drzwi podwójnych: po `doors_per_car` na człon, na obie strony."""
        doors = []
        for index in range(self.cars):
            start, end = self.door_usable_span(index)
            step = (end - start) / self.doors_per_car
            if step < self.door_width:
                raise ValueError(f"człon {index}: {self.doors_per_car} drzwi nie mieści się w {end - start:.2f} m")
            for slot in range(self.doors_per_car):
                center = start + (slot + 0.5) * step
                for side in (1, -1):
                    doors.append({
                        "kind": "double",
                        "car": index,
                        "side": side,
                        "center_x": round(center, 6),
                        "width": self.door_width,
                        "x0": round(center - self.door_width / 2.0, 6),
                        "x1": round(center + self.door_width / 2.0, 6),
                        "z0": self.floor_z,
                        "z1": round(self.floor_z + DESIGN_DOOR_OPENING_HEIGHT_M, 6),
                    })
        return doors

    def cab_doors_list(self):
        """Pojedyncze drzwi kabinowe: po jednych na kabinę, układ obrotowo symetryczny."""
        if self.cab_doors != 2:
            raise ValueError(f"generator zakłada 2 drzwi kabinowe, spec podaje {self.cab_doors}")
        entries = []
        for end_index, (center, side) in enumerate((
                (DESIGN_CAB_DOOR_CENTER_FROM_END_M, 1),
                (self.length - DESIGN_CAB_DOOR_CENTER_FROM_END_M, -1))):
            entries.append({
                "kind": "cab",
                "car": 0 if end_index == 0 else self.cars - 1,
                "side": side,
                "center_x": round(center, 6),
                "width": DESIGN_CAB_DOOR_WIDTH_M,
                "x0": round(center - DESIGN_CAB_DOOR_WIDTH_M / 2.0, 6),
                "x1": round(center + DESIGN_CAB_DOOR_WIDTH_M / 2.0, 6),
                "z0": self.floor_z,
                "z1": round(self.floor_z + DESIGN_CAB_DOOR_HEIGHT_M, 6),
            })
        return entries

    def all_doors(self):
        return self.double_doors() + self.cab_doors_list()

    # --- przekrój -------------------------------------------------------------

    def taper(self, x):
        """Zwraca (inset_na_stronę, obniżenie_dachu) dla danego X — tylko ścięcie czoła."""
        distance = min(x, self.length - x)
        if distance >= DESIGN_NOSE_LENGTH_M:
            return 0.0, 0.0
        ratio = 1.0 - distance / DESIGN_NOSE_LENGTH_M
        return DESIGN_NOSE_INSET_M * ratio, DESIGN_NOSE_ROOF_DROP_M * ratio

    def section(self, x, extra_inset=0.0):
        """Przekrój poprzeczny w płaszczyźnie YZ: prostokąt ze ściętym dachem."""
        inset, drop = self.taper(x)
        half = self.half_width - inset - extra_inset
        top = self.roof_z - drop
        chamfer = min(DESIGN_ROOF_CHAMFER_M, half * 0.9, (top - self.body_bottom_z) * 0.4)
        bottom = self.body_bottom_z
        return [
            (-half, bottom), (half, bottom),
            (half, top - chamfer), (half - chamfer, top),
            (-half + chamfer, top), (-half, top - chamfer),
        ]

    def section_extent(self, x, extra_inset=0.0):
        points = self.section(x, extra_inset)
        ys = [p[0] for p in points]
        zs = [p[1] for p in points]
        return min(ys), min(zs), max(ys), max(zs)

    # --- kontrola skrajni -----------------------------------------------------

    def fits_vehicle_gauge(self, samples=200):
        """Czy bryła mieści się w projektowej skrajni pojazdu z profiles.py."""
        gauge = profiles.vehicle_gauge(clearance=0.0)
        gy = [p[0] for p in gauge]
        gz = [p[1] for p in gauge]
        for i in range(samples + 1):
            x = self.length * i / samples
            y0, z0, y1, z1 = self.section_extent(x)
            if y0 < min(gy) - 1e-9 or y1 > max(gy) + 1e-9:
                return False, f"x={x:.2f}: szerokość {y1 - y0:.3f} m poza skrajnią"
            if z0 < min(gz) - 1e-9 or z1 > max(gz) + 1e-9:
                return False, f"x={x:.2f}: wysokość {z1:.3f} m poza skrajnią"
        return True, "ok"

    def fits_tunnel_profiles(self):
        """Czy skrajnia pojazdu mieści się w każdym istniejącym profilu tunelu."""
        report = {}
        for name in profiles.PROFILES:
            ok, message = profiles.fits_gauge(name)
            report[name] = {"ok": ok, "message": message, "min_clearance_m": profiles.min_clearance(name) if ok else 0.0}
        return report

    # --- podsumowanie ---------------------------------------------------------

    def summary(self):
        doubles = self.double_doors()
        return {
            "spec": self.spec,
            "design_assumptions": {k: v[0] for k, v in DESIGN_ASSUMPTIONS.items()},
            "length_m": self.length,
            "width_m": self.width,
            "height_m": self.roof_z,
            "floor_height_m": self.floor_z,
            "body_bottom_z_m": round(self.body_bottom_z, 6),
            "cars": self.cars,
            "car_length_m": round(self.car_length, 6),
            "doors_per_car_per_side": self.doors_per_car,
            "double_doors_total": len(doubles),
            "double_doors_per_side": len(doubles) // 2,
            "cab_doors_total": len(self.cab_doors_list()),
            "articulations": len(self.articulation_spans()),
        }


def report():
    layout = Layout()
    summary = layout.summary()
    lines = [f"M7 shell — {summary['length_m']} x {summary['width_m']} m, {summary['cars']} członów",
             f"człon: {summary['car_length_m']:.4f} m, drzwi/człon/stronę: {summary['doors_per_car_per_side']}",
             f"drzwi podwójne: {summary['double_doors_per_side']} na stronę, {summary['double_doors_total']} razem",
             f"drzwi kabinowe: {summary['cab_doors_total']}"]
    ok, message = layout.fits_vehicle_gauge()
    lines.append(f"skrajnia pojazdu: {'OK' if ok else message}")
    for name, entry in layout.fits_tunnel_profiles().items():
        lines.append(f"  {name:<14} {'OK' if entry['ok'] else entry['message']} luz_max={entry['min_clearance_m']:.2f} m")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
