#!/usr/bin/env python3
"""Mapa kilometrażu sieci z osi pakietów: pokrycie, dziury i kolizje w planie.

    python3 tools/track/network_chainage.py --out build/network-chainage.json

Pakiety są jednostką BUDOWY, nie jazdy. Każda oś zaczyna kilometraż od zera, a między
pakietami zostają odcinki, których nikt nie zbudował. Skład jadący całą linią 1
przekracza granicę pakietu i musi wiedzieć, gdzie ta granica jest i co za nią leży.

Narzędzie odpowiada na trzy pytania, wszystkie pomiarem:

1. **Co pokrywa która oś** — pakiet, linia, zakres kilometrażu, stacje graniczne.
2. **Gdzie są dziury** — pary stacji leżących po dwóch stronach granicy pakietu
   i odległość między końcami osi. To NIE jest długość brakującego toru, tylko
   cięciwa: brakującego odcinka nie ma w `data/track/`, więc nie da się go zmierzyć
   wzdłuż trasy. Długości wzdłuż łamanej źródłowej są w
   `reports/packages-BF-alignment.md` §8.
3. **Gdzie osie kolidują w planie** — miejsca, w których dwie osie są bliżej niż
   szerokość profilu tunelu. Przy `vertical.status = "not_modelled"` cała sieć leży
   na Z = 0, więc tam, gdzie linie krzyżują się w rzeczywistości na różnych
   poziomach, w modelu **dwie rury przechodzą przez siebie**. To jest wejście dla
   T-112 i dla sceny, która wczyta więcej niż jeden pakiet naraz.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import crosscheck_alignment as CC  # noqa: E402
import provenance as P  # noqa: E402

DEFAULT_AXES = ["L1_A", "L1_B", "L5_C", "L5_D", "L2_E", "L6_F"]
# Szerokość profilu `box_double`. Dwie osie bliżej niż to mają w modelu nachodzące
# na siebie rury — przy Z = 0 dosłownie, bo nic ich pionowo nie rozdziela.
DEFAULT_CONFLICT_M = 9.40
# Poniżej tego uznajemy, że osie biegną RÓWNOLEGLE (sąsiednie tory tej samej relacji),
# a nie że się krzyżują. Rozstaw torów w projekcie to 4,20 m, korytarze sąsiednich
# linii bywają kilkanaście metrów od siebie.
PARALLEL_M = 30.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Mapa kilometrażu sieci z osi pakietów")
    parser.add_argument("--axes", default=",".join(DEFAULT_AXES),
                        help="identyfikatory osi z data/track, po przecinku")
    parser.add_argument("--conflict-m", type=float, default=DEFAULT_CONFLICT_M)
    parser.add_argument("--parallel-m", type=float, default=PARALLEL_M)
    parser.add_argument("--out", required=True)
    return parser.parse_args(argv)


def chainages(points):
    values = [0.0]
    for a, b in zip(points, points[1:]):
        values.append(values[-1] + math.dist(a, b))
    return values


def distance_to_axis(point, points):
    return min(CC._distance_to_polyline(point, [a, b]) for a, b in zip(points, points[1:]))


def nearest_station(document, chainage):
    stations = document.get("stations") or []
    if not stations:
        return None
    best = min(stations, key=lambda s: abs(float(s["chainage_m"]) - chainage))
    return {"name": best["name"], "offset_m": round(chainage - float(best["chainage_m"]), 1)}


def load_axes(names):
    axes = {}
    for name in names:
        path = os.path.join(ROOT, "data", "track", f"{name}.json")
        document, points = CC.load_alignment(path)
        axes[name] = {"document": document, "points": points,
                      "chainages": chainages(points)}
    return axes


def coverage(axes):
    """Co pokrywa która oś — bez interpretacji, wprost z plików."""
    rows = []
    for name, entry in axes.items():
        document = entry["document"]
        package = document.get("package") or {}
        rows.append({
            "axis_id": name,
            "line": name.split("_")[0],
            "package": package.get("id"),
            "package_name": package.get("name"),
            "from_station": package.get("from"),
            "to_station": package.get("to"),
            "length_m": round(entry["chainages"][-1], 2),
            "declared_length_m": document.get("length_m"),
            "stations": len(document.get("stations") or []),
            "vertical_status": (document.get("vertical") or {}).get("status"),
        })
    return sorted(rows, key=lambda r: (r["line"], r["package"] or ""))


def endpoint_gaps(axes, conflict_m):
    """Dziury między pakietami — mierzone jako cięciwa między końcami osi.

    Świadomie NIE nazywamy tego długością brakującego toru: odcinków między pakietami
    nie ma w `data/track/`, więc nie da się ich zmierzyć wzdłuż trasy. Cięciwa jest
    dolnym ograniczeniem i tyle o niej wiadomo.
    """
    ends = {}
    for name, entry in axes.items():
        package = entry["document"].get("package") or {}
        ends[name] = {
            "start": {"point": entry["points"][0], "station": package.get("from")},
            "end": {"point": entry["points"][-1], "station": package.get("to")},
        }
    gaps = []
    names = sorted(axes)
    # Każda para końców RAZ: pętla po i < j, nie po wszystkich uporządkowanych parach.
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for a_side in ("start", "end"):
                for b_side in ("start", "end"):
                    chord = math.dist(ends[a][a_side]["point"], ends[b][b_side]["point"])
                    if chord > 2000.0:
                        continue
                    gaps.append({
                        "from_axis": a, "from_side": a_side,
                        "from_station": ends[a][a_side]["station"],
                        "to_axis": b, "to_side": b_side,
                        "to_station": ends[b][b_side]["station"],
                        "chord_m": round(chord, 1),
                        "same_station": ends[a][a_side]["station"] == ends[b][b_side]["station"],
                    })
    return sorted(gaps, key=lambda g: g["chord_m"])


def proximity(axes, conflict_m, parallel_m):
    """Gdzie dwie osie są bliżej niż szerokość profilu — czyli gdzie rury się przenikają.

    Rozróżniamy dwa przypadki, bo znaczą co innego: osie biegnące RÓWNOLEGLE w jednym
    korytarzu (sąsiednie linie na wspólnym odcinku) i osie KRZYŻUJĄCE się. Pierwsze są
    faktem o sieci; drugie są artefaktem braku niwelety, bo w rzeczywistości krzyżują
    się na różnych poziomach.
    """
    rows = []
    names = sorted(axes)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = axes[a]["points"], axes[b]["points"]
            ca, cb = axes[a]["chainages"], axes[b]["chainages"]
            near_a = [distance_to_axis(p, pb) for p in pa]
            corridor = [d <= parallel_m for d in near_a]
            conflict = [d < conflict_m for d in near_a]
            if not any(corridor):
                continue
            hits = [(d, c) for d, c in zip(near_a, ca) if d < conflict_m]
            entry = {
                "axis_a": a, "axis_b": b,
                "corridor_ranges_a_m": CC.chainage_ranges(pa, corridor),
                "corridor_ranges_b_m": CC.chainage_ranges(
                    pb, [distance_to_axis(p, pa) <= parallel_m for p in pb]),
                "conflict_points": len(hits),
                "conflict_ranges_a_m": CC.chainage_ranges(pa, conflict),
                "min_distance_m": round(min(near_a), 2),
            }
            entry["conflicts"] = [
                {"chainage_a_m": round(c, 1), "distance_m": round(d, 2),
                 "nearest_station_a": nearest_station(axes[a]["document"], c)}
                for d, c in sorted(hits)[:10]
            ]
            corridor_len = sum(hi - lo for lo, hi in entry["corridor_ranges_a_m"])
            entry["corridor_length_a_m"] = round(corridor_len, 1)
            rows.append(entry)
    return rows


def survey(args):
    names = [n.strip() for n in args.axes.split(",") if n.strip()]
    axes = load_axes(names)
    rows = coverage(axes)
    total = round(sum(r["length_m"] for r in rows), 1)
    return {
        "checked_at": P.utc_now_iso(),
        "axes": names,
        "conflict_threshold_m": args.conflict_m,
        "parallel_threshold_m": args.parallel_m,
        "coverage": rows,
        "total_axis_length_m": total,
        "endpoint_gaps": endpoint_gaps(axes, args.conflict_m),
        "proximity": proximity(axes, args.conflict_m, args.parallel_m),
        "note": ("Cięciwa między końcami pakietów NIE jest długością brakującego toru — "
                 "odcinków międzypakietowych nie ma w data/track. Kolizje w planie są "
                 "artefaktem vertical.status = not_modelled: przy Z = 0 nic nie rozdziela "
                 "pionowo linii, które w rzeczywistości krzyżują się na różnych poziomach."),
    }


def main(argv=None):
    args = parse_args(argv)
    report = survey(args)
    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    print(f"[SIEĆ] {len(report['coverage'])} osi, razem {report['total_axis_length_m']} m")
    for row in report["coverage"]:
        print(f"[SIEĆ]   {row['axis_id']:6} pakiet {row['package']}  "
              f"{row['from_station']} -> {row['to_station']}  "
              f"{row['length_m']:8.1f} m, {row['stations']} stacji")
    print(f"[SIEĆ] granice pakietów: {len(report['endpoint_gaps'])} par końców bliżej niż 2 km")
    for gap in report["endpoint_gaps"][:8]:
        print(f"[SIEĆ]   {gap['from_axis']}.{gap['from_side']} ({gap['from_station']}) -> "
              f"{gap['to_axis']}.{gap['to_side']} ({gap['to_station']}): "
              f"cięciwa {gap['chord_m']} m")
    if not report["proximity"]:
        print("[SIEĆ] żadne dwie osie nie zbliżają się na próg równoległości")
    for entry in report["proximity"]:
        print(f"[SIEĆ] {entry['axis_a']} x {entry['axis_b']}: wspólny korytarz "
              f"{entry['corridor_length_a_m']} m, minimum {entry['min_distance_m']} m, "
              f"punktów w kolizji {entry['conflict_points']}")
        for conflict in entry["conflicts"][:4]:
            station = conflict["nearest_station_a"] or {}
            print(f"[SIEĆ]     {conflict['distance_m']:6.2f} m @ "
                  f"{conflict['chainage_a_m']:8.1f} m "
                  f"(~{station.get('name')} {station.get('offset_m'):+.0f} m)")
    print(f"[SIEĆ] zapisano {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
