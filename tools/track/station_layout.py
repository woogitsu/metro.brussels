#!/usr/bin/env python3
"""Rozmieszczenie peronów wzdłuż osi — połowa danych, zero decyzji projektowych.

    python3 tools/track/station_layout.py --axis data/track/L1_A.json \
        --out build/L1_A-platforms.json --platform-length-m 94.0

Ten sam podział, co w T-011: **tu liczą się kilometraże i granice**, a bryły buduje
osobne narzędzie w Blenderze. Pierwsza połowa nie ma ani jednej decyzji projektowej
i testuje się bez Blendera.

Co ten plik liczy i skąd to bierze:

* **położenie peronu** — wyśrodkowane na kilometrażu stacji z osi (T-011 poprawił ten
  kilometraż tak, żeby był liczony na tej samej łamanej, która trafia do pliku);
* **minimalne odsunięcie krawędzi** — pół szerokości M7 plus strzałka cięciwy członu
  na lokalnym promieniu. Sztywne pudło opiera się na łuku cięciwą, więc jego środek
  wchodzi do wnętrza łuku; peron postawiony bliżej byłby w kolizji. To jest DOLNA
  GRANICA policzona z geometrii, a nie wymiar peronu.

Czego ten plik NIE robi:

* **nie wymyśla szczeliny peron–pudło.** R-007 (`reports/R-007-platform-dimensions.md`)
  ustalił, że nie podaje jej żadne publiczne źródło. `--platform-gap-m` NIE MA wartości
  domyślnej: bez niej `edge_offset_m` wychodzi `None`, a nie liczba. Zero znaczyłoby
  „peron dotyka pudła", a nie „nie wiem";
* **nie bierze `platform_edge_x` z profilu `station`.** Zmierzone: przy torach na
  ±2,10 m i krawędziach na ±4,05 m szczelina wychodzi **0,600 m**, bo 1,95 = 1,35
  (pół szerokości M7) + 2 × 0,30 (`CLEARANCE_M`). To jest granica skrajni, nie krawędź
  peronu — 60 cm szczeliny to przepaść, do której wpada noga;
* **nie modeluje wychylenia zewnętrznego końców składu** — wymaga rozstawu czopów
  skrętu, którego nie ma w `m7-spec.json` (to samo zastrzeżenie, co w `clearance.py`).
"""
import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import clearance as CL  # noqa: E402
import profiles  # noqa: E402
import sweep as SW  # noqa: E402

#: Krok zagęszczania osi, ten sam co w generatorze tuneli i w rdzeniu.
RING_STEP_M = 5.0


def _spec():
    with open(os.path.join(ROOT, "data", "vehicle", "m7-spec.json"), encoding="utf-8") as handle:
        return json.load(handle)["parameters"]


def train_length_m():
    """Długość składu M7 — `spec` w rejestrze, źródło STIB."""
    entry = _spec()["length_m"]
    if entry["status"] != "spec":
        raise SystemExit(
            f"length_m ma status '{entry['status']}', a dolna granica długości peronu "
            "musi stać na fakcie, nie na założeniu")
    return float(entry["value"])


def platform_height_m():
    """Wysokość peronu = wysokość podłogi M7.

    STIB pisze, że podłoga M7 jest „à hauteur du quai" (R-007), więc to nie są dwie
    liczby, tylko jedna. Czytana z rejestru, żeby nie było drugiej kopii.
    """
    entry = _spec()["floor_height_m"]
    return float(entry["value"]), entry["status"]


def radius_within(points, chord_m, from_m, to_m):
    """Najmniejszy promień na odcinku peronu; None, gdy odcinek jest prosty."""
    radii = [r for s, r in CL.radii_along(points, chord_m)
             if r is not None and from_m <= s <= to_m]
    return min(radii) if radii else None


def layout(axis_document, platform_length_m, platform_gap_m=None, footprint_m=None,
           ring_step_m=RING_STEP_M):
    """Perony wszystkich stacji osi. Bez `platform_gap_m` odsunięcie zostaje `None`."""
    points = SW.catmull_rom(
        [tuple(float(c) for c in p) for p in axis_document["points"]], ring_step_m)
    axis_length_m = SW.chainages(points)[-1]
    chord_m = CL.car_chord_m({"length_m": train_length_m(), "cars": int(_spec()["cars"]["value"])})
    half_width_m = profiles.M7_WIDTH_M / 2.0
    height_m, height_status = platform_height_m()

    minimum = train_length_m()
    if platform_length_m < minimum:
        raise SystemExit(
            f"peron {platform_length_m:.2f} m jest krótszy od składu M7 ({minimum:.2f} m); "
            "R-007 wyprowadza z tego dolną granicę, bo STIB nie stosuje selektywnego "
            "otwierania drzwi")

    platforms = []
    for station in axis_document.get("stations", []):
        centre = float(station["chainage_m"])
        raw_from = centre - platform_length_m / 2.0
        raw_to = centre + platform_length_m / 2.0
        start = max(0.0, raw_from)
        end = min(axis_length_m, raw_to)
        radius = radius_within(points, chord_m, start, end)
        versine_m = CL.versine(chord_m, radius)
        minimum_offset_m = half_width_m + versine_m

        record = {
            "name": station.get("name"),
            "stop_id": station.get("stop_id"),
            "station_chainage_m": round(centre, 3),
            "from_m": round(start, 3),
            "to_m": round(end, 3),
            "length_m": round(end - start, 3),
            "clipped_at_start": raw_from < -1e-9,
            "clipped_at_end": raw_to > axis_length_m + 1e-9,
            "min_radius_m": round(radius, 2) if radius else None,
            "versine_m": round(versine_m, 4),
            "minimum_edge_offset_m": round(minimum_offset_m, 4),
            "edge_offset_m": (round(minimum_offset_m + platform_gap_m, 4)
                              if platform_gap_m is not None else None),
            "height_m": height_m,
            "height_status": height_status,
        }
        if footprint_m is not None:
            record["footprint_m"] = footprint_m
            record["within_footprint"] = record["length_m"] <= footprint_m + 1e-9
        platforms.append(record)

    return {
        "axis_id": axis_document.get("id"),
        "axis_length_m": round(axis_length_m, 3),
        "ring_step_m": ring_step_m,
        "platform_length_m": platform_length_m,
        "platform_length_basis": (
            "R-007: brak źródła długości peronu; dolna granica to długość składu M7 "
            "(94,0 m, spec STIB), górna to obrys stacji (najciaśniej Parc 109,1 m)"),
        "platform_gap_m": platform_gap_m,
        "platform_gap_basis": (
            "brak źródła (R-007) — bez --platform-gap-m odsunięcie krawędzi zostaje null"),
        "car_chord_m": round(chord_m, 4),
        "m7_half_width_m": half_width_m,
        "platform_height_m": height_m,
        "platform_height_status": height_status,
        "not_modelled": [
            "wychylenie zewnętrzne końców składu — brak rozstawu czopów skrętu w m7-spec.json",
            "przechyłka, ugięcie zawieszenia, tolerancje toru",
            "szczelina peron–pudło — brak źródła publicznego (R-007)",
        ],
        "platforms": platforms,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rozmieszczenie peronów wzdłuż osi")
    parser.add_argument("--axis", required=True)
    parser.add_argument("--out")
    parser.add_argument("--platform-length-m", type=float, default=None,
                        help="domyślnie długość składu M7 — dolna granica z R-007")
    parser.add_argument("--platform-gap-m", type=float, default=None,
                        help="szczelina peron–pudło; BEZ WARTOŚCI DOMYŚLNEJ, bo nie ma źródła")
    parser.add_argument("--footprint-m", type=float, default=None,
                        help="górna granica długości z obrysu stacji; kontrola, nie wymiar")
    parser.add_argument("--ring-step-m", type=float, default=RING_STEP_M)
    args = parser.parse_args(argv)

    with open(args.axis, encoding="utf-8") as handle:
        document = json.load(handle)

    length = args.platform_length_m if args.platform_length_m is not None else train_length_m()
    report = layout(document, length, args.platform_gap_m, args.footprint_m, args.ring_step_m)

    clipped = sum(1 for p in report["platforms"] if p["clipped_at_start"] or p["clipped_at_end"])
    offsets = [p["minimum_edge_offset_m"] for p in report["platforms"]]
    print(f"[PERONY] {report['axis_id']}: {len(report['platforms'])} peronów po "
          f"{report['platform_length_m']:.2f} m na osi {report['axis_length_m']:.1f} m")
    print(f"[PERONY] wysokość {report['platform_height_m']:.2f} m "
          f"({report['platform_height_status']}), cięciwa członu {report['car_chord_m']:.3f} m")
    print(f"[PERONY] minimalne odsunięcie krawędzi {min(offsets):.4f}–{max(offsets):.4f} m "
          f"(pół szerokości {report['m7_half_width_m']:.2f} m + strzałka na łuku)")
    if report["platform_gap_m"] is None:
        print("[PERONY] szczelina peron–pudło NIE PODANA — edge_offset_m zostaje null, "
              "bo zero znaczyłoby „peron dotyka pudła\"")
    if clipped:
        print(f"[PERONY] {clipped} peronów przyciętych do końca osi")
    outside = [p["name"] for p in report["platforms"] if p.get("within_footprint") is False]
    if outside:
        print(f"[PERONY] BŁĄD: peron dłuższy niż obrys stacji: {outside}")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
        print(f"[RAPORT] {args.out}")
    return 1 if outside else 0


if __name__ == "__main__":
    sys.exit(main())
