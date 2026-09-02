#!/usr/bin/env python3
"""Kontrola renderów: sanity, metryki i porównanie z baseline. Bez ciężkich zależności.

Trzy poziomy kontroli, w tej kolejności:

1. `exists` / `dimension` — plik istnieje i ma rozdzielczość z manifestu;
2. `not_empty` — obraz nie jest czarny, pusty ani jednolitym tłem;
3. `regression` — różnica względem baseline: MAE, percentyl 95 i uproszczone SSIM.

Baseline NIGDY nie jest nadpisywany automatycznie. Brak baseline daje status
`new-baseline`, który przechodzi tylko przy jawnym `--allow-new-baseline`,
a zapis wymaga osobnego `--accept-baseline`.

Metryka automatyczna nie zastępuje obejrzenia PNG (CLAUDE.md §5).
"""
import argparse
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngio

BACKGROUND_TOLERANCE = 0.02

# Podłoga „to nie jest pusta klatka" dla renderów bez manifestu i bez baseline.
# Wartości są NAJŁAGODNIEJSZYM zestawem progów już używanym w `cameras.json`
# (infrastructure / alignment / clearance), więc podłoga nie może odrzucić kadru,
# który w pipeline wizualnym przechodzi. Pilnuje tego test w `test_visual.py`.
EMPTY_FRAME_FLOOR = {
    "min_ink_fraction": 0.0002,
    "min_luma_std": 0.004,
    "min_distinct_levels": 16,
}
SSIM_WIDTH = 128
SSIM_WINDOW = 8
C1 = 0.01 ** 2
C2 = 0.03 ** 2


def downsample(img, target_w=SSIM_WIDTH):
    """Uśrednianie blokowe do stałej szerokości — tłumi szum renderera."""
    target_w = min(target_w, img.width)
    target_h = max(1, int(round(img.height * target_w / img.width)))
    out = [0.0] * (target_w * target_h)
    for ty in range(target_h):
        y0 = int(ty * img.height / target_h)
        y1 = max(y0 + 1, int((ty + 1) * img.height / target_h))
        for tx in range(target_w):
            x0 = int(tx * img.width / target_w)
            x1 = max(x0 + 1, int((tx + 1) * img.width / target_w))
            total = 0.0
            count = 0
            for y in range(y0, y1):
                base = y * img.width
                total += sum(img.gray[base + x0:base + x1])
                count += x1 - x0
            out[ty * target_w + tx] = total / count
    return target_w, target_h, out


def image_stats(img):
    """Statystyki wystarczające, by odróżnić render od czarnej/pustej klatki."""
    histogram = [0] * 256
    for value in img.gray:
        histogram[min(255, max(0, int(value * 255.0)))] += 1
    background = histogram.index(max(histogram)) / 255.0
    total = len(img.gray)
    ink = sum(1 for value in img.gray if abs(value - background) > BACKGROUND_TOLERANCE)
    mean = sum(img.gray) / total
    variance = sum((value - mean) ** 2 for value in img.gray) / total
    return {
        "width": img.width,
        "height": img.height,
        "luma_mean": round(mean, 6),
        "luma_std": round(math.sqrt(variance), 6),
        "background_level": round(background, 4),
        "ink_fraction": round(ink / total, 6),
        "distinct_levels": sum(1 for count in histogram if count),
    }


def empty_frame_reason(stats, thresholds):
    """Powód, dla którego klatka jest pusta/jednorodna — albo `None`, gdy nie jest.

    Wydzielone z `check_image`, bo tej samej kontroli potrzebuje render kontrolny
    z `tools/blender/render_check.py`: on nie ma ani manifestu, ani baseline, a to
    właśnie tam pusty PNG przechodził z kodem wyjścia 0.

    "Nie-pusty" nie może być samym pokryciem tła: render tunelu z daleka to włos
    w kadrze, a widok z wnętrza wypełnia kadr geometrią, więc modalny poziom JEST
    geometrią. Pusta klatka to klatka jednorodna: zero wariancji i kilka poziomów.
    """
    if (stats["ink_fraction"] >= thresholds["min_ink_fraction"]
            and stats["luma_std"] >= thresholds["min_luma_std"]
            and stats["distinct_levels"] >= thresholds["min_distinct_levels"]):
        return None
    return (f"obraz pusty/jednorodny: ink={stats['ink_fraction']:.5f} "
            f"std={stats['luma_std']:.5f} poziomy={stats['distinct_levels']}")


def ssim(a_w, a_h, a, b):
    """Uproszczone globalne SSIM na oknach 8x8 zdecymowanego obrazu."""
    scores = []
    for wy in range(0, a_h - SSIM_WINDOW + 1, SSIM_WINDOW):
        for wx in range(0, a_w - SSIM_WINDOW + 1, SSIM_WINDOW):
            xs, ys = [], []
            for y in range(wy, wy + SSIM_WINDOW):
                base = y * a_w
                xs.extend(a[base + wx:base + wx + SSIM_WINDOW])
                ys.extend(b[base + wx:base + wx + SSIM_WINDOW])
            n = len(xs)
            mx = sum(xs) / n
            my = sum(ys) / n
            vx = sum((v - mx) ** 2 for v in xs) / n
            vy = sum((v - my) ** 2 for v in ys) / n
            cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / n
            scores.append(((2 * mx * my + C1) * (2 * cov + C2)) / ((mx * mx + my * my + C1) * (vx + vy + C2)))
    return sum(scores) / len(scores) if scores else 1.0


def diff_metrics(current, baseline):
    if current.size != baseline.size:
        raise ValueError("rozmiary obrazów różne — metryki różnicowe nie mają sensu")
    diffs = [abs(c - b) for c, b in zip(current.gray, baseline.gray)]
    diffs_sorted = sorted(diffs)
    cw, ch, cd = downsample(current)
    _, _, bd = downsample(baseline)
    return {
        "mean_abs_diff": round(sum(diffs) / len(diffs), 8),
        "p95_abs_diff": round(diffs_sorted[int(0.95 * (len(diffs_sorted) - 1))], 8),
        "max_abs_diff": round(diffs_sorted[-1], 8),
        "changed_fraction": round(sum(1 for d in diffs if d > 0.02) / len(diffs), 8),
        "ssim": round(ssim(cw, ch, cd, bd), 8),
    }


def write_diff_image(path, current, baseline, amplify=4.0):
    gray = [min(1.0, abs(c - b) * amplify) for c, b in zip(current.gray, baseline.gray)]
    pngio.write_gray(path, current.width, current.height, gray)


def check_image(path, expected_size, thresholds, baseline_path=None, diff_path=None):
    result = {"current": path, "baseline": baseline_path, "checks": {}, "metrics": {}}
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        result["checks"]["exists"] = False
        result["status"] = "fail"
        result["reason"] = "brak pliku renderu albo plik pusty"
        return result
    result["checks"]["exists"] = True
    img = pngio.read_gray(path)
    stats = image_stats(img)
    result["metrics"].update(stats)

    size_ok = list(img.size) == list(expected_size)
    result["checks"]["dimension"] = size_ok
    empty = empty_frame_reason(stats, thresholds)
    result["checks"]["not_empty"] = empty is None

    if not size_ok:
        result["status"] = "fail"
        result["reason"] = f"rozdzielczość {img.size} != oczekiwana {tuple(expected_size)}"
        return result
    if empty is not None:
        result["status"] = "fail"
        result["reason"] = empty
        return result

    if not baseline_path or not os.path.isfile(baseline_path):
        result["status"] = "new-baseline"
        result["reason"] = "brak canonical baseline — wymaga jawnego zatwierdzenia"
        return result

    base = pngio.read_gray(baseline_path)
    if base.size != img.size:
        result["checks"]["baseline_dimension"] = False
        result["status"] = "fail"
        result["reason"] = f"baseline ma rozmiar {base.size}, render {img.size}"
        return result
    result["checks"]["baseline_dimension"] = True
    metrics = diff_metrics(img, base)
    result["metrics"].update(metrics)
    regressed = (metrics["mean_abs_diff"] > thresholds["mean_abs_diff"]
                 or metrics["p95_abs_diff"] > thresholds["p95_abs_diff"]
                 or metrics["ssim"] < thresholds["ssim_min"])
    result["checks"]["regression"] = not regressed
    if regressed and diff_path:
        os.makedirs(os.path.dirname(diff_path) or ".", exist_ok=True)
        write_diff_image(diff_path, img, base)
        shutil.copyfile(path, diff_path.replace("_diff.png", "_current.png"))
        shutil.copyfile(baseline_path, diff_path.replace("_diff.png", "_before.png"))
        result["artifacts"] = {
            "diff": diff_path,
            "current": diff_path.replace("_diff.png", "_current.png"),
            "before": diff_path.replace("_diff.png", "_before.png"),
        }
    result["status"] = "fail" if regressed else "pass"
    if regressed:
        result["reason"] = (f"regresja: MAE={metrics['mean_abs_diff']:.5f} "
                            f"p95={metrics['p95_abs_diff']:.5f} SSIM={metrics['ssim']:.5f}")
    return result


GEOMETRY_TOLERANCE_M = 0.001
# Eksporter glTF dzieli wierzchołki na duplikaty w innej kolejności przy każdym
# przebiegu, więc liczba wierzchołków po imporcie GLB NIE jest niezmiennikiem
# regenerowanego assetu: ta sama geometria M7 (2334 unikalne pozycje, 4732 ściany,
# różnica 0) dała 5360 i 5386 wierzchołków po imporcie. Bbox i liczba obiektów są
# odtwarzalne dokładnie, więc zostają twarde; liczniki dostają tolerancję względną,
# która nadal łapie realną zmianę gęstości siatki.
GEOMETRY_COUNT_TOLERANCE = 0.10


def check_geometry(current_meta, baseline_meta, tolerance=GEOMETRY_TOLERANCE_M,
                   count_tolerance=GEOMETRY_COUNT_TOLERANCE):
    """Kontrola wymiarowa z metadanych: kadr jest względny, bbox nie.

    Metryka obrazowa nie wykryje przesunięcia całego modelu, bo kamera kadruje się
    względem bboxa i jedzie razem z nim. Bezwzględna geometria musi więc być
    porównywana liczbowo, a nie na obrazku.
    """
    result = {"tolerance_m": tolerance, "count_tolerance_ratio": count_tolerance,
              "checks": {}, "current": current_meta, "baseline": baseline_meta}
    if not current_meta or not os.path.isfile(current_meta):
        result["status"] = "fail"
        result["reason"] = "brak metadanych bieżącego przebiegu"
        return result
    with open(current_meta, encoding="utf-8") as handle:
        current = json.load(handle)
    result["scene"] = current.get("scene")
    result["blender_version"] = current.get("blender_version")
    result["manifest_version"] = current.get("manifest_version")
    if not baseline_meta or not os.path.isfile(baseline_meta):
        result["status"] = "new-baseline"
        result["reason"] = "brak metadanych baseline"
        return result
    with open(baseline_meta, encoding="utf-8") as handle:
        base = json.load(handle)

    deltas = {}
    for key in ("bbox_min", "bbox_max", "size_m"):
        cur_v = current["scene"][key]
        base_v = base["scene"][key]
        delta = [round(a - b, 6) for a, b in zip(cur_v, base_v)]
        deltas[key] = delta
        result["checks"][key] = all(abs(d) <= tolerance for d in delta)
    result["deltas_m"] = deltas
    result["checks"]["mesh_objects"] = current["scene"]["mesh_objects"] == base["scene"]["mesh_objects"]
    counts = {}
    for key in ("vertices", "faces"):
        cur_v = current["scene"][key]
        base_v = base["scene"][key]
        allowed = max(1.0, base_v * count_tolerance)
        counts[key] = {"current": cur_v, "baseline": base_v, "delta": cur_v - base_v,
                       "allowed_delta": round(allowed, 3)}
        result["checks"][key] = abs(cur_v - base_v) <= allowed
    result["counts"] = counts
    result["checks"]["manifest_version"] = current.get("manifest_version") == base.get("manifest_version")
    result["checks"]["blender_version"] = current.get("blender_version") == base.get("blender_version")
    result["checks"]["resolution"] = current.get("resolution") == base.get("resolution")

    failed = [k for k, ok in result["checks"].items() if not ok]
    result["status"] = "fail" if failed else "pass"
    if failed:
        result["reason"] = "różnice: " + ", ".join(failed)
    return result


def load_manifest(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def run(manifest, set_name, current_dir, prefix, baseline_dir, diff_dir, cameras=None):
    scene_set = manifest["scene_sets"][set_name]
    thresholds = scene_set["thresholds"]
    expected = scene_set["resolution"]
    ids = cameras if cameras else [c["id"] for c in scene_set["cameras"]]
    entries = []
    for camera_id in ids:
        name = f"{prefix}_{camera_id}.png"
        baseline_path = os.path.join(baseline_dir, name) if baseline_dir else None
        diff_path = os.path.join(diff_dir, f"{prefix}_{camera_id}_diff.png") if diff_dir else None
        entry = check_image(os.path.join(current_dir, name), expected, thresholds, baseline_path, diff_path)
        entry["camera"] = camera_id
        entries.append(entry)
    meta_name = f"{prefix}_metadata.json"
    geometry = check_geometry(os.path.join(current_dir, meta_name),
                              os.path.join(baseline_dir, meta_name) if baseline_dir else None)
    return {
        "manifest_version": manifest.get("manifest_version"),
        "scene_set": set_name,
        "prefix": prefix,
        "thresholds": thresholds,
        "expected_resolution": expected,
        "images": entries,
        "geometry": geometry,
    }


def main():
    parser = argparse.ArgumentParser(description="Porównanie renderów kontrolnych z baseline")
    parser.add_argument("--manifest", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cameras.json"))
    parser.add_argument("--set", dest="scene_set", required=True)
    parser.add_argument("--current", required=True, help="katalog z bieżącymi renderami")
    parser.add_argument("--prefix", required=True, help="przedrostek nazw plików, np. M7_shell")
    parser.add_argument("--baseline", help="katalog z canonical baseline")
    parser.add_argument("--diff-dir", help="katalog na before/current/diff przy regresji")
    parser.add_argument("--cameras", help="ograniczenie do wybranych kamer, po przecinku")
    parser.add_argument("--out", help="ścieżka raportu JSON")
    parser.add_argument("--markdown", help="ścieżka raportu Markdown")
    parser.add_argument("--allow-new-baseline", action="store_true",
                        help="brak baseline nie jest błędem (świadoma decyzja w zadaniu)")
    parser.add_argument("--accept-baseline", action="store_true",
                        help="skopiuj bieżące rendery do baseline; nigdy nie dzieje się automatycznie")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    cameras = [c.strip() for c in args.cameras.split(",")] if args.cameras else None
    report = run(manifest, args.scene_set, args.current, args.prefix, args.baseline, args.diff_dir, cameras)

    entries = report["images"] + [report["geometry"]]
    failed = [e for e in entries if e["status"] == "fail"]
    fresh = [e for e in entries if e["status"] == "new-baseline"]
    report["summary"] = {
        "total": len(entries),
        "pass": sum(1 for e in entries if e["status"] == "pass"),
        "fail": len(failed),
        "new_baseline": len(fresh),
    }
    report["status"] = "fail" if failed or (fresh and not args.allow_new_baseline) else "pass"

    if args.accept_baseline:
        if failed:
            print("BŁĄD: nie zatwierdzam baseline, gdy są obrazy z błędem sanity", file=sys.stderr)
            return 2
        if not args.baseline:
            print("BŁĄD: --accept-baseline wymaga --baseline", file=sys.stderr)
            return 2
        os.makedirs(args.baseline, exist_ok=True)
        for entry in report["images"]:
            shutil.copyfile(entry["current"], os.path.join(args.baseline, os.path.basename(entry["current"])))
        report["baseline_accepted"] = True
        print(f"[BASELINE] zatwierdzono {len(report['images'])} obrazów w {args.baseline}")

    for entry in report["images"]:
        metrics = entry.get("metrics", {})
        extra = ""
        if "ssim" in metrics:
            extra = f" MAE={metrics['mean_abs_diff']:.5f} p95={metrics['p95_abs_diff']:.5f} SSIM={metrics['ssim']:.5f}"
        print(f"  {entry['status']:<12} {entry['camera']:<10} ink={metrics.get('ink_fraction', 0):.4f}"
              f" std={metrics.get('luma_std', 0):.4f}{extra}"
              + (f"  <- {entry['reason']}" if entry.get("reason") else ""))

    geometry = report["geometry"]
    print(f"  {geometry['status']:<12} {'geometria':<10} "
          + (f"delta_m={geometry.get('deltas_m', {}).get('size_m')}" if "deltas_m" in geometry else "")
          + (f"  <- {geometry['reason']}" if geometry.get("reason") else ""))

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(f"[RAPORT] {args.out}")
    if args.markdown:
        os.makedirs(os.path.dirname(args.markdown) or ".", exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as handle:
            handle.write(to_markdown(report))
        print(f"[RAPORT] {args.markdown}")

    print(f"[WYNIK] {report['status']} — {report['summary']}")
    return 0 if report["status"] == "pass" else 1


def to_markdown(report):
    lines = [f"# Kontrola wizualna — {report['prefix']} ({report['scene_set']})", "",
             f"- manifest: `{report['manifest_version']}`",
             f"- oczekiwana rozdzielczość: {report['expected_resolution'][0]}x{report['expected_resolution'][1]}",
             f"- wynik: **{report['status']}** {report['summary']}", "",
             "| kamera | status | ink | luma_std | MAE | p95 | SSIM | uwaga |",
             "|---|---|---:|---:|---:|---:|---:|---|"]
    for entry in report["images"]:
        m = entry.get("metrics", {})
        lines.append("| {c} | {s} | {ink} | {std} | {mae} | {p95} | {ssim} | {r} |".format(
            c=entry["camera"], s=entry["status"],
            ink=f"{m.get('ink_fraction', 0):.4f}", std=f"{m.get('luma_std', 0):.4f}",
            mae=f"{m['mean_abs_diff']:.5f}" if "mean_abs_diff" in m else "—",
            p95=f"{m['p95_abs_diff']:.5f}" if "p95_abs_diff" in m else "—",
            ssim=f"{m['ssim']:.5f}" if "ssim" in m else "—",
            r=entry.get("reason", "")))
    geometry = report.get("geometry", {})
    lines += ["", f"Kontrola wymiarowa z metadanych: **{geometry.get('status', 'brak')}**"
                  + (f" — {geometry['reason']}" if geometry.get("reason") else ""), ""]
    lines += ["Metryka automatyczna nie zastępuje obejrzenia PNG (CLAUDE.md §5)."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
