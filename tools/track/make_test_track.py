#!/usr/bin/env python3
"""
Generuje syntetyczną oś trasy do testów narzędzi.

    python3 tools/track/make_test_track.py --out build/t010/TEST.json
    python3 tools/track/make_test_track.py --out build/t010/BROKEN.json --broken
"""
import json, math, argparse, os

def build(broken=False):
    pts, stations = [], []
    n, step = 260, 8.0
    st_at = {0: "Stacja A", 120: "Stacja B", 259: "Stacja C"}
    for i in range(n):
        s = i * step
        x = s
        y = 120 * math.sin(s / 420.0)
        z = -14.0 - 2.5 * math.sin(s / 330.0) ** 2 * 2
        if broken and i == 130:
            z = -30.0
        pts.append([round(x, 3), round(y, 3), round(z, 3)])
        if i in st_at:
            stations.append({"name": st_at[i], "chainage_m": round(s, 1), "depth_m": round(z, 2), "interpolated": True})
    if broken:
        pts[200] = [pts[199][0] + 60, pts[199][1], pts[199][2]]
    return {"id": "TEST", "crs": "syntetyczny, origin (0,0)", "points": pts, "stations": stations,
            "speed_limits": [{"from_m": 0, "to_m": 400, "kmh": 50}, {"from_m": 400, "to_m": 2000, "kmh": 70}]}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--broken", action="store_true", help="wstaw celowe błędy")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    d = build(a.broken)
    json.dump(d, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"zapisano {a.out}: {len(d['points'])} punktów, {len(d['stations'])} stacji" + (" (Z BŁĘDAMI)" if a.broken else ""))
