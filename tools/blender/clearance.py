"""Skrajnia M7 na rzeczywistych łukach: czy projektowy profil tunelu wytrzymuje.

    python3 tools/blender/clearance.py --alignment data/track/L1_A.json --profile box_double

Czysty Python, bez bpy. `profiles.fits_gauge` sprawdza skrajnię **na prostej**; tutaj
dochodzi to, co robi łuk: sztywne pudło członu opiera się na łuku cięciwą, więc jego
środek wchodzi do wnętrza łuku o strzałkę cięciwy.

Czego ten model NIE liczy, świadomie:

- **wychylenia zewnętrznego na końcach składu** — wymaga rozstawu czopów skrętu, którego
  nie ma w `data/vehicle/m7-spec.json`; T-220 celowo nie wymyślił wózków (#14);
- przechyłki, ugięcia zawieszenia, zużycia kół, tolerancji toru;
- rozjazdów i odcinków przejściowych.

Dlatego wynik jest **warunkiem koniecznym**, nie pełną skrajnią kinematyczną. Ujemny
zapas oznacza „na pewno nie mieści się"; dodatni oznacza „na tym poziomie modelu mieści się".

Promień nie jest daną, tylko oszacowaniem, więc raportowane są **widełki**:

- `pessimistic` — mierzony na skomitowanej łamanej, której ostre wierzchołki zaniżają promień;
- `optimistic` — mierzony na krzywej zagęszczonej, która wygładza te wierzchołki.

Prawdziwy tor leży gdzieś pomiędzy. Werdykt zapada na **wariancie pesymistycznym**:
profil, który przechodzi tylko po wygładzeniu, nie jest profilem, na którym można polegać.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import m7_layout  # noqa: E402
import profiles  # noqa: E402
import sweep  # noqa: E402

#: Odstęp, przy którym dwa niemieszczące się punkty należą jeszcze do tego samego
#: przedziału. Punkty osi stoją co 7,6-22,4 m (zmierzone na sześciu osiach
#: `data/track/`), więc próg musi być powyżej największego z tych odstępów.
SPAN_GAP_M = 25.0


def versine(chord_m, radius_m):
    """Strzałka cięciwy: o ile środek sztywnego pudła wchodzi do wnętrza łuku."""
    if radius_m is None or radius_m <= 0.0:
        return 0.0
    half = chord_m / 2.0
    if half >= radius_m:
        return radius_m
    return radius_m - math.sqrt(radius_m * radius_m - half * half)


def car_chord_m(spec):
    """Cięciwa jednego członu. `length_m` i `cars` są ze specyfikacji, równy podział nie."""
    return float(spec["length_m"]) / int(spec["cars"])


def circumradius(a, b, c):
    """Promień okręgu opisanego na trzech punktach; None dla współliniowych."""
    ab = math.dist(a, b)
    bc = math.dist(b, c)
    ca = math.dist(c, a)
    area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    # Warunek `ab * bc * ca == 0.0` stał tu obok i był MARTWY: iloczyn zeruje się
    # tylko wtedy, gdy dwa punkty się pokrywają, a wtedy `area2` też jest zerem
    # i pierwszy warunek już odrzuca trójkę. Przegląd mutacyjny 02.09.2026 pokazał
    # to wprost — mutacja tego zera przeżywała, bo nie da się jej zaobserwować.
    if area2 < 1e-12:
        return None
    return ab * bc * ca / (2.0 * area2)


def radii_along(points, chord_m):
    """Promień w każdym punkcie, mierzony na cięciwie długości pudła członu.

    Trójka sąsiednich wierzchołków osi daje promień lokalnego szumu digitalizacji,
    a nie łuku, po którym faktycznie stanie pudło. Bierzemy więc punkty odległe
    o pół cięciwy w obie strony — dokładnie to, co „widzi" człon.
    """
    stations = sweep.chainages(points)
    out = []
    half = chord_m / 2.0
    for index, station in enumerate(stations):
        before = _point_at(points, stations, station - half)
        after = _point_at(points, stations, station + half)
        if before is None or after is None:
            continue
        radius = circumradius(before[:2], points[index][:2], after[:2])
        out.append((station, radius))
    return out


def _point_at(points, stations, target):
    if target < stations[0] or target > stations[-1]:
        return None
    for index in range(len(stations) - 1):
        if stations[index] <= target <= stations[index + 1]:
            span = stations[index + 1] - stations[index]
            t = 0.0 if span <= 0.0 else (target - stations[index]) / span
            a, b = points[index], points[index + 1]
            return tuple(a[i] + t * (b[i] - a[i]) for i in range(3))
    return points[-1]


def margin_at(profile_name, chord_m, radius_m, static_clearance_m):
    """Zapas skrajni w JEDNYM punkcie o zadanym promieniu.

    Wielkością odejmowaną jest strzałka cięciwy, nie szerokość pojazdu: skrajnia
    pojazdu jest inflatowana o `versine`, a M7 zostaje taka, jaka jest
    (`test_clearance_never_shrinks_the_train_to_make_it_fit`).
    """
    needed = versine(chord_m, radius_m)
    fits, message = profiles.fits_gauge(profile_name, needed)
    return needed, static_clearance_m - needed, bool(fits), message


def merge_spans(stations, gap_m):
    """Kilometraże w rosnącej kolejności sklejone w przedziały.

    Dwa sąsiednie punkty osi dzieli 7,6-22,4 m, więc punkty tej samej dziury
    w skrajni muszą się skleić w JEDEN przedział, inaczej raport podaje trzydzieści
    „miejsc", w których nie przechodzi, zamiast jednego.
    """
    spans = []
    for station in sorted(stations):
        if spans and station - spans[-1][1] <= gap_m:
            spans[-1][1] = station
        else:
            spans.append([station, station])
    return [(round(lo, 1), round(hi, 1)) for lo, hi in spans]


def scan(points, profile_name, chord_m, span_gap_m=SPAN_GAP_M):
    """Skrajnia sprawdzona W KAŻDYM punkcie osi, nie tylko w najciaśniejszym łuku.

    `evaluate` odpowiada na pytanie „czy przechodzi w najgorszym miejscu" i to
    wystarcza do werdyktu, bo strzałka rośnie monotonicznie, gdy promień maleje.
    Nie wystarcza jednak do opisu osi: nie mówi, ILE punktów jest ciasnych ani
    GDZIE leżą. Ten przebieg woła `profiles.fits_gauge` osobno w każdym punkcie,
    czyli nie zakłada monotoniczności, tylko ją sprawdza.
    """
    available = profiles.min_clearance(profile_name)
    samples = [(s, r) for s, r in radii_along(points, chord_m) if r is not None]
    margins = []
    failing = []
    for station, radius in samples:
        _needed, margin, fits, _message = margin_at(profile_name, chord_m, radius,
                                                    available)
        margins.append((station, radius, margin, fits))
        if not fits:
            failing.append((station, margin))
    worst = min(margins, key=lambda item: item[2]) if margins else None
    shortfall = min((m for _s, m in failing), default=None)
    return {
        "profile": profile_name,
        "static_clearance_m": available,
        "samples": len(margins),
        "failing_samples": len(failing),
        "fits_everywhere": not failing,
        "min_margin_m": round(worst[2], 4) if worst else None,
        "min_margin_chainage_m": round(worst[0], 1) if worst else None,
        "min_margin_radius_m": round(worst[1], 2) if worst else None,
        "worst_shortfall_m": round(shortfall, 4) if shortfall is not None else None,
        "failing_spans_m": merge_spans([s for s, _m in failing], span_gap_m),
    }


def evaluate(points, profile_name, chord_m):
    """Najgorszy punkt osi: najmniejszy promień i wynikający z niego zapas skrajni."""
    available = profiles.min_clearance(profile_name)
    samples = [(s, r) for s, r in radii_along(points, chord_m) if r is not None]
    worst_station, worst_radius = min(samples, key=lambda item: item[1]) if samples else (0.0, None)
    needed = versine(chord_m, worst_radius)
    fits, message = profiles.fits_gauge(profile_name, needed)
    radii = sorted(r for _s, r in samples)
    return {
        "profile": profile_name,
        "car_chord_m": round(chord_m, 4),
        "static_clearance_m": available,
        "min_radius_m": round(worst_radius, 2) if worst_radius else None,
        "min_radius_chainage_m": round(worst_station, 1),
        "p05_radius_m": round(radii[int(0.05 * (len(radii) - 1))], 2) if radii else None,
        "median_radius_m": round(radii[len(radii) // 2], 2) if radii else None,
        "versine_at_min_radius_m": round(needed, 4),
        "margin_m": round(available - needed, 4),
        "fits_on_curve": bool(fits),
        "fits_message": message,
        "samples": len(samples),
        "not_modelled": [
            "wychylenie zewnętrzne końców składu — brak rozstawu czopów skrętu w m7-spec.json",
            "przechyłka, ugięcie zawieszenia, zużycie kół, tolerancje toru",
            "rozjazdy i odcinki przejściowe",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Skrajnia M7 na łukach rzeczywistej osi")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--profile", default="box_double", choices=list(profiles.PROFILES))
    parser.add_argument("--ring-step", type=float, default=5.0,
                        help="zagęszczenie osi dla wariantu optymistycznego")
    parser.add_argument("--out", help="ścieżka na wynik JSON")
    parser.add_argument("--report-only", action="store_true",
                        help="nie kończ błędem, gdy profil nie przechodzi — tylko zaraportuj")
    parser.add_argument("--scan", action="store_true",
                        help="sprawdź skrajnię punkt po punkcie, nie tylko w najciaśniejszym łuku")
    args = parser.parse_args(argv)

    path = args.alignment if os.path.isabs(args.alignment) else os.path.join(ROOT, args.alignment)
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    source = [tuple(p) for p in document["points"]]

    spec = m7_layout.load_spec()
    chord = car_chord_m(spec)
    pessimistic = evaluate(source, args.profile, chord)
    optimistic = evaluate(sweep.catmull_rom(source, args.ring_step), args.profile, chord)

    result = {
        "alignment": document.get("id", os.path.basename(path)),
        "profile": args.profile,
        "car_chord_m": round(chord, 4),
        "ring_step_m": args.ring_step,
        "static_clearance_m": pessimistic["static_clearance_m"],
        "pessimistic": pessimistic,
        "optimistic": optimistic,
        "verdict_from": "pessimistic",
        "fits_on_curve": pessimistic["fits_on_curve"],
        "vehicle": {"length_m": spec["length_m"], "cars": spec["cars"],
                    "width_m": spec["width_m"],
                    "car_split": "design_assumption: równy podział"},
    }

    print(f"[SKRAJNIA] oś={result['alignment']} profil={args.profile} "
          f"człon={chord:.3f} m ({spec['cars']} x, {spec['length_m']} m)")
    print(f"[SKRAJNIA] statyczny zapas profilu: {result['static_clearance_m']:.3f} m")
    for name in ("pessimistic", "optimistic"):
        item = result[name]
        print(f"[SKRAJNIA] {name:11s}: Rmin {item['min_radius_m']} m @ {item['min_radius_chainage_m']} m, "
              f"P05 {item['p05_radius_m']} m, strzałka {item['versine_at_min_radius_m']*1000:.1f} mm, "
              f"zapas {item['margin_m']:+.3f} m -> {'MIEŚCI SIĘ' if item['fits_on_curve'] else 'NIE MIEŚCI SIĘ'}")
    if args.scan:
        result["scan"] = {
            "pessimistic": scan(source, args.profile, chord),
            "optimistic": scan(sweep.catmull_rom(source, args.ring_step), args.profile, chord),
        }
        for name in ("pessimistic", "optimistic"):
            item = result["scan"][name]
            shortfall = ("brak" if item["worst_shortfall_m"] is None
                         else f"{item['worst_shortfall_m']:+.4f} m")
            print(f"[PUNKT PO PUNKCIE] {name:11s}: {item['samples']} punktów, "
                  f"nie przechodzi {item['failing_samples']}, "
                  f"najmniejszy zapas {item['min_margin_m']:+.4f} m "
                  f"@ {item['min_margin_chainage_m']} m (R {item['min_margin_radius_m']} m), "
                  f"niedobór {shortfall}")
            if item["failing_spans_m"]:
                spans = "; ".join(f"{lo}-{hi} m" for lo, hi in item["failing_spans_m"])
                print(f"[PUNKT PO PUNKCIE] {name:11s}: przedziały bez skrajni: {spans}")

    for item in pessimistic["not_modelled"]:
        print(f"[SKRAJNIA] nieliczone: {item}")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"[RAPORT] {args.out}")

    if not result["fits_on_curve"]:
        message = (f"skrajnia M7 nie mieści się w {args.profile} na najciaśniejszym łuku "
                   f"(wariant pesymistyczny, zapas {pessimistic['margin_m']:+.3f} m)")
        if args.report_only:
            print(f"[SKRAJNIA] UWAGA: {message}")
            return 0
        raise SystemExit("BŁĄD: " + message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
