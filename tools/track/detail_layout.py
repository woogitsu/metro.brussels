#!/usr/bin/env python3
"""Rozstawianie detali wzdłuż osi: gdzie, a nie jak wygląda.

    python3 tools/track/detail_layout.py --axis data/track/L1_A.json \
        --out build/L1_A-details.json --brake-from-kmh 72

**Podział, z którego wynika reszta.** Ten moduł liczy wyłącznie **kilometraże** —
listę miejsc, w których coś ma stanąć, wraz z powodem. Nie wie nic o geometrii
znacznika, jego rozmiarze ani kolorze; to należy do `tools/blender/detail_markers.py`
i jest tam jawnym założeniem wołającego. Dzięki temu ta połowa zadania nie ma
**ani jednej** decyzji estetycznej i daje się przetestować bez Blendera.

Trzy rodzaje miejsc:

* `hectometre` — co 100 m od początku osi. Konwencja kolejowa, nie wybór;
* `station` — kilometraż stacji z `data/track/*.json`, z nazwą i `stop_id`;
* `brake` — punkt, w którym trzeba zacząć hamować, żeby stanąć na stacji.
  Jedyny rodzaj, który wymaga założenia: prędkości, z której hamujemy.
  Nie ma wartości domyślnej — patrz `--brake-from-kmh`.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import braking as B  # noqa: E402
import provenance as P  # noqa: E402

#: Odstęp słupków kilometrażu. Konwencja kolejowa (hektometr), nie decyzja projektowa.
HECTOMETRE_STEP_M = 100.0

#: Kilometraże bliższe sobie niż tyle uznajemy za to samo miejsce. Wartość wynika
#: z zapisu: `chainage_m` w osi jest zaokrąglone do centymetra, więc rozróżnianie
#: czegokolwiek poniżej byłoby rozróżnianiem szumu zapisu.
SAME_PLACE_M = 0.01

#: Najdłuższa oś, jaką ten projekt może w ogóle dostać. Cała sieć metra to 39,9 km
#: (`data/network/lines.json`, pole `network.metro_length_km`), a oś jest fragmentem
#: jednej linii — więc 40 km jest granicą od góry dla czegokolwiek, co tu wejdzie.
MAX_AXIS_LENGTH_M = 40000.0

#: Najgęstszy krok, przy którym siatka hektometrowa jeszcze cokolwiek znaczy.
#: Konwencja kolejowa to 100 m; 1 m jest już sto razy gęstsze i nie jest
#: „hektometrem" w żadnym sensie.
MIN_SENSIBLE_STEP_M = 1.0

#: Ogranicznik liczby znaczników, **niezależny od strażnika `step_m`**. Strażnik
#: sprawdza znak kroku i był jedyną rzeczą, która trzymała pętlę w `hectometre_marks`:
#: przy `step_m == 0.0` warunek `index * step_m <= length_m` jest prawdziwy zawsze,
#: więc jego osłabienie nie dawało złego wyniku, tylko proces, który się nie kończy
#: (przemiatanie mutacyjne 03.09.2026: `timeout 20` kończył się kodem 124, czyli
#: mutacja nie mogła nawet zostać zaraportowana jako zabita).
#:
#: Liczba: 40 km / 1 m. Najdłuższa realna oś pakietu to 6,7 km, co przy konwencyjnym
#: kroku 100 m daje 68 znaczników — ogranicznik jest od tego ~590 razy wyżej, więc
#: nie da się w niego wejść poprawnym wejściem. Przekroczenie podnosi `ValueError`
#: z liczbami, a nie ucina wyniku po cichu: ucięta siatka wygląda dokładnie tak samo
#: jak krótka oś.
MAX_MARKS = int(MAX_AXIS_LENGTH_M / MIN_SENSIBLE_STEP_M)


def hectometre_marks(length_m, step_m=HECTOMETRE_STEP_M):
    """Kilometraże co `step_m`, od zera, **bez** przekraczania końca osi.

    Znacznik dokładnie na końcu osi jest dopuszczony: koniec osi to ostatnia stacja,
    więc taki znacznik i tak zniknie przy scaleniu ze stacjami.

    Pętlę trzymają DWA warunki, każdy sam z siebie wystarczający do jej zakończenia:
    strażnik `step_m > 0` i ogranicznik `MAX_MARKS`. Ogranicznik nie jest zapasem
    na wypadek błędu — jest jedynym powodem, dla którego ta funkcja zatrzymuje się
    także wtedy, gdy strażnik zniknie. Przekroczenie go to `ValueError`, nie ucięcie.
    """
    if step_m <= 0.0:
        raise ValueError("krok hektometrów musi być dodatni")
    marks = []
    index = 0
    while index * step_m <= length_m + SAME_PLACE_M:
        if index >= MAX_MARKS:
            raise ValueError(
                f"siatka hektometrów przekroczyła {MAX_MARKS} znaczników: krok "
                f"{step_m} m na osi {length_m} m. Granica to {MAX_AXIS_LENGTH_M:.0f} m "
                f"sieci przez {MIN_SENSIBLE_STEP_M:.0f} m najgęstszego sensownego "
                f"kroku; najdłuższy pakiet (6686 m) daje przy kroku "
                f"{HECTOMETRE_STEP_M:.0f} m 68 znaczników")
        marks.append(round(index * step_m, 2))
        index += 1
    return marks


def braking_distance_m(speed_mps, decel_mps2, jerk_mps3):
    """Droga hamowania z T-311, z ograniczeniem zrywu. Zero dla postoju."""
    if speed_mps <= 0.0:
        return 0.0
    if decel_mps2 >= B.plateau_ceiling_mps2(speed_mps, 0.0, jerk_mps3):
        # Cel wypada w trakcie narastania hamulca — zadane `b` nigdy nie działa.
        return B.ramp_only_distance_m(speed_mps, 0.0, jerk_mps3)
    return B.braking_distance_m(speed_mps, 0.0, decel_mps2, jerk_mps3)


def braking_marks(stations, speed_mps, decel_mps2, jerk_mps3):
    """Punkty hamowania przed każdą stacją, poza pierwszą.

    Punkt, który wypadłby **przed poprzednią stacją**, jest pomijany z podanym
    powodem, a nie przesuwany: znaczyłby, że skład miałby zacząć hamować, zanim
    ruszył, więc na tym odcinku prędkość z założenia jest nieosiągalna.
    """
    distance = braking_distance_m(speed_mps, decel_mps2, jerk_mps3)
    marks, skipped = [], []
    for previous, station in zip(stations, stations[1:]):
        point = station["chainage_m"] - distance
        if point <= previous["chainage_m"] + SAME_PLACE_M:
            skipped.append({
                "station": station["name"],
                "chainage_m": round(station["chainage_m"], 2),
                "would_be_at_m": round(point, 2),
                "previous_station_at_m": round(previous["chainage_m"], 2),
                "reason": "punkt hamowania wypada przed poprzednią stacją — przy tej "
                          "prędkości odcinek jest za krótki, żeby ją osiągnąć",
            })
            continue
        marks.append({"chainage_m": round(point, 2), "kind": "brake",
                      "label": station["name"], "for_station": station["name"],
                      "braking_distance_m": round(distance, 2)})
    return marks, skipped


def layout(axis, speed_mps=None, decel_mps2=None, jerk_mps3=None, step_m=HECTOMETRE_STEP_M):
    """Pełna lista miejsc wzdłuż osi, posortowana, bez duplikatów.

    Pierwszeństwo ma znacznik **bardziej znaczący**: stacja bije punkt hamowania,
    punkt hamowania bije hektometr. Dwa znaczniki w tym samym miejscu byłyby dwoma
    słupkami w jednym punkcie.
    """
    length = float(axis["length_m"])
    stations = sorted(axis.get("stations", []), key=lambda s: s["chainage_m"])

    entries = [{"chainage_m": round(s["chainage_m"], 2), "kind": "station",
                "label": s["name"], "stop_id": s.get("stop_id", "")}
               for s in stations]
    skipped = []
    if speed_mps is not None:
        marks, skipped = braking_marks(stations, speed_mps, decel_mps2, jerk_mps3)
        entries.extend(marks)
    entries.extend({"chainage_m": c, "kind": "hectometre", "label": f"{c / 1000.0:.1f}"}
                   for c in hectometre_marks(length, step_m))

    rank = {"station": 0, "brake": 1, "hectometre": 2}
    entries.sort(key=lambda e: (e["chainage_m"], rank[e["kind"]]))

    kept = []
    for entry in entries:
        if kept and abs(entry["chainage_m"] - kept[-1]["chainage_m"]) <= SAME_PLACE_M:
            continue
        kept.append(entry)
    return kept, skipped


def survey(axis, axis_id, speed_kmh=None, step_m=HECTOMETRE_STEP_M, cfg=None):
    cfg = cfg if cfg is not None else B.params()
    speed_mps = None if speed_kmh is None else speed_kmh / 3.6
    marks, skipped = layout(axis, speed_mps, cfg["service"], cfg["jerk"], step_m)
    counts = {}
    for entry in marks:
        counts[entry["kind"]] = counts.get(entry["kind"], 0) + 1
    return {
        "checked_at": P.utc_now_iso(),
        "axis_id": axis_id,
        "axis_length_m": round(float(axis["length_m"]), 3),
        "hectometre_step_m": step_m,
        "brake_from_kmh": speed_kmh,
        "service_brake_mps2": cfg["service"] if speed_kmh is not None else None,
        "jerk_mps3": cfg["jerk"] if speed_kmh is not None else None,
        "braking_distance_m": None if speed_kmh is None else round(
            braking_distance_m(speed_mps, cfg["service"], cfg["jerk"]), 2),
        "counts": counts,
        "marks": marks,
        "skipped_brake_points": skipped,
        "note": ("Ten plik podaje WYŁĄCZNIE kilometraże. Rozmiar, kształt i strona "
                 "znacznika są założeniem wołającego i mieszkają w "
                 "tools/blender/detail_markers.py."),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Rozstawianie detali wzdłuż osi")
    parser.add_argument("--axis", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--step-m", type=float, default=HECTOMETRE_STEP_M)
    parser.add_argument("--brake-from-kmh", type=float,
                        help="prędkość, z której liczony jest punkt hamowania. BEZ "
                             "wartości domyślnej: prędkość dopuszczalna na torze nie ma "
                             "źródła (R-006), więc scenariusz musi ją zadeklarować sam. "
                             "Pominięta = bez punktów hamowania.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    path = args.axis if os.path.isabs(args.axis) else os.path.join(ROOT, args.axis)
    with open(path, encoding="utf-8") as handle:
        axis = json.load(handle)

    report = survey(axis, axis["id"], args.brake_from_kmh, args.step_m)
    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    counts = report["counts"]
    print(f"[DETALE] {report['axis_id']}: {report['axis_length_m']:.1f} m osi, "
          f"{len(report['marks'])} miejsc — "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if report["brake_from_kmh"] is not None:
        print(f"[DETALE] punkt hamowania: {report['brake_from_kmh']:.0f} km/h, "
              f"hamulec {report['service_brake_mps2']:.2f} m/s², zryw "
              f"{report['jerk_mps3']:.2f} m/s³ -> {report['braking_distance_m']:.2f} m")
    for entry in report["skipped_brake_points"]:
        print(f"[DETALE] pominięty punkt hamowania przed {entry['station']}: wypadłby na "
              f"{entry['would_be_at_m']:.2f} m, a poprzednia stacja jest na "
              f"{entry['previous_station_at_m']:.2f} m")
    print(f"[DETALE] zapisano {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
