#!/usr/bin/env python3
"""Konfrontacja rozkładu STIB z modelem fizyki M7 — koperta prędkości liniowej.

    python3 tools/physics/schedule_envelope.py --timetable build/timetable.json \
        --out build/schedule-envelope.json

**Po co.** W repo nie ma ani jednego źródła na prędkość liniową sieci. `speed_limits`
w każdej osi z T-210 jest pustą listą, a `max_speed_kmh` = 80 w rejestrze M7 ma
`status: design_model` i `source_id: null` — jest to prędkość konstrukcyjna pojazdu
przepisana z legacy symulatora, a nie prędkość dopuszczalna na torze.

Rozkład pozwala tę dziurę **ograniczyć od dołu, pomiarem**. Dla odcinka o zmierzonej
długości `L` i rozkładowym czasie jazdy `T` szukamy najmniejszej prędkości szczytowej
`v`, przy której profil rozpęd–jazda–hamowanie mieści się w `T`. Ponieważ

    czas_fizyczny(v_rzeczywista) <= czas_rzeczywisty <= T_rozkładowy

a `czas_fizyczny` maleje z `v`, każda `v` mniejsza od znalezionej **nie zdążyłaby**.
Znaleziona liczba jest więc dolnym ograniczeniem prędkości dopuszczalnej na tym
odcinku, a nie jej pomiarem. Rozkład zawiera rezerwę, więc prawdziwa prędkość jest
wyższa — ograniczenie jest zachowawcze w obie strony.

**Czego to nie dowodzi.** Ograniczenie jest warunkowe względem modelu rozpędzania
i hamowania, a ten model jest w całości `design_model`: krzywa trakcyjna z T-310
i hamulec służbowy 1,10 m/s² z `docs/02-simulation.md`. Gdyby M7 rozpędzał się
mocniej, ta sama rozkładowa jazda wyszłaby przy niższej prędkości szczytowej.
Liczba mówi „przy tym modelu nie da się wolniej", a nie „tak jeździ metro".

Ani jednej liczby o pojeździe nie ma tu wklejonej — wszystkie idą z rejestru przez
`tools/physics/braking.py`, a rozpędzanie liczy zamrożona referencja parytetu T-310
(`tools/physics/reference.py`), żeby nie powstała trzecia implementacja fizyki.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import braking as B  # noqa: E402
import reference as R  # noqa: E402

#: Krok bisekcji po prędkości; 40 podziałów schodzi poniżej 0,001 km/h na zakresie 0–120.
BISECTION_STEPS = 40
#: Górny kres poszukiwań. Nie jest twierdzeniem o sieci — jest sufitem przeszukiwania,
#: świadomie wyższym niż konstrukcyjne 80 km/h, żeby odcinek nierealizowalny wyszedł
#: jako nierealizowalny, a nie jako „dokładnie 80".
SEARCH_CEILING_KMH = 120.0


def brake_profile(v0_ms, decel, jerk):
    """Droga i czas hamowania do zera. Poniżej sufitu plateau obowiązuje sam zryw."""
    if v0_ms <= 0.0:
        return 0.0, 0.0
    if decel >= B.plateau_ceiling_mps2(v0_ms, 0.0, jerk):
        # Cel wypada w trakcie narastania hamulca — zadane `b` nigdy nie zostaje osiągnięte.
        distance = B.ramp_only_distance_m(v0_ms, 0.0, jerk)
        return distance, (2.0 * (v0_ms) / jerk) ** 0.5
    return (B.braking_distance_m(v0_ms, 0.0, decel, jerk),
            B.braking_time_s(v0_ms, 0.0, decel, jerk))


class Model:
    """Rozpęd z referencji T-310 i hamowanie z rejestru, z pamięcią podręczną."""

    def __init__(self, mass_kg, cfg):
        self.mass_kg = mass_kg
        self.decel = cfg["service"]
        self.jerk = cfg["jerk"]
        self._accel = {}

    def accel(self, v_kmh):
        key = round(v_kmh, 6)
        if key not in self._accel:
            self._accel[key] = R.sim_accel(self.mass_kg, key)
        return self._accel[key]

    def brake(self, v_kmh):
        return brake_profile(v_kmh / 3.6, self.decel, self.jerk)

    def peak_speed_kmh(self, distance_m, ceiling_kmh):
        """Najwyższa prędkość osiągalna na odcinku: rozpęd i hamowanie stykają się."""
        low, high = 0.0, ceiling_kmh
        for _ in range(BISECTION_STEPS):
            mid = 0.5 * (low + high)
            _t_a, s_a = self.accel(mid)
            s_b, _t_b = self.brake(mid)
            if s_a + s_b > distance_m:
                high = mid
            else:
                low = mid
        return low

    def fastest_time_s(self, distance_m, v_top_kmh):
        """Najkrótszy czas jazdy na odcinku przy suficie prędkości `v_top_kmh`."""
        t_a, s_a = self.accel(v_top_kmh)
        s_b, t_b = self.brake(v_top_kmh)
        if s_a + s_b <= distance_m:
            return t_a + (distance_m - s_a - s_b) / (v_top_kmh / 3.6) + t_b
        peak = self.peak_speed_kmh(distance_m, v_top_kmh)
        t_a, _s_a = self.accel(peak)
        _s_b, t_b = self.brake(peak)
        return t_a + t_b

    def minimum_top_speed_kmh(self, distance_m, scheduled_s, ceiling_kmh=SEARCH_CEILING_KMH):
        """Najmniejszy sufit prędkości mieszczący się w rozkładzie; None = nie mieści się."""
        if self.fastest_time_s(distance_m, ceiling_kmh) > scheduled_s:
            return None
        low, high = 0.0, ceiling_kmh
        for _ in range(BISECTION_STEPS):
            mid = 0.5 * (low + high)
            if mid <= 0.0:
                break
            if self.fastest_time_s(distance_m, mid) > scheduled_s:
                low = mid
            else:
                high = mid
        return high


def envelope(timetable, mass_key, cfg, ceiling_kmh=SEARCH_CEILING_KMH):
    mass_kg = cfg["aw0_kg"] if mass_key == "AW0" else cfg["aw2_kg"]
    model = Model(mass_kg, cfg)

    rows = []
    seen = set()
    for segment in timetable["segments"]:
        if "distance_m" not in segment:
            continue
        key = (segment["package"], segment["from_stop"], segment["to_stop"])
        if key in seen:
            # Ten sam odcinek toru obsługiwany przez dwie linie (pień 1/5, pierścień 2/6)
            # ma ten sam rozkładowy czas jazdy; liczymy go raz.
            continue
        seen.add(key)
        distance = segment["distance_m"]
        scheduled = float(segment["median_s"])
        required = model.minimum_top_speed_kmh(distance, scheduled, ceiling_kmh)
        floor_time = model.fastest_time_s(distance, ceiling_kmh)
        rows.append({
            "package": segment["package"],
            "line": segment["line"],
            "direction_id": segment["direction_id"],
            "from_name": segment["from_name"],
            "to_name": segment["to_name"],
            "distance_m": distance,
            "scheduled_s": scheduled,
            "unconstrained_time_s": round(floor_time, 2),
            "reserve_vs_unconstrained_s": round(scheduled - floor_time, 2),
            "min_top_speed_kmh": None if required is None else round(required, 2),
            "feasible": required is not None,
        })

    rows.sort(key=lambda row: (-1.0 if row["min_top_speed_kmh"] is None
                               else -row["min_top_speed_kmh"]))
    feasible = [row for row in rows if row["feasible"]]
    binding = feasible[0] if feasible else None
    return {
        "mass_case": mass_key,
        "mass_kg": mass_kg,
        "service_brake_mps2": cfg["service"],
        "jerk_mps3": cfg["jerk"],
        "search_ceiling_kmh": ceiling_kmh,
        "segments": len(rows),
        "infeasible": sum(1 for row in rows if not row["feasible"]),
        "network_min_top_speed_kmh": binding["min_top_speed_kmh"] if binding else None,
        "binding_segment": binding,
        "rows": rows,
        "note": ("min_top_speed_kmh to DOLNE ograniczenie prędkości dopuszczalnej, warunkowe "
                 "względem modelu rozpędzania z T-310 i hamulca służbowego z docs/02 — "
                 "obu design_model. Rozkład zawiera rezerwę, więc prędkość rzeczywista jest "
                 "wyższa. Nie jest to pomiar prędkości liniowej sieci."),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Koperta prędkości z rozkładu i fizyki")
    parser.add_argument("--timetable", default=os.path.join("build", "timetable.json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--mass", choices=("AW0", "AW2"), default="AW0")
    parser.add_argument("--ceiling-kmh", type=float, default=SEARCH_CEILING_KMH)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    source = args.timetable if os.path.isabs(args.timetable) else os.path.join(ROOT, args.timetable)
    with open(source, encoding="utf-8") as handle:
        timetable = json.load(handle)
    if not any("distance_m" in s for s in timetable["segments"]):
        raise SystemExit("BŁĄD: rozkład nie ma odległości wzdłuż osi — uruchom "
                         "tools/track/timetable.py z --axis")

    report = envelope(timetable, args.mass, B.params(), args.ceiling_kmh)
    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    print(f"[KOPERTA] {report['segments']} odcinków, masa {report['mass_case']} "
          f"{report['mass_kg']:.0f} kg, hamulec {report['service_brake_mps2']:.2f} m/s², "
          f"zryw {report['jerk_mps3']:.2f} m/s³")
    for row in report["rows"]:
        speed = "NIEREALIZOWALNY" if row["min_top_speed_kmh"] is None \
            else f"{row['min_top_speed_kmh']:6.2f} km/h"
        print(f"[KOPERTA] {row['package']} {row['from_name']} → {row['to_name']}: "
              f"{row['distance_m']:7.1f} m, rozkład {row['scheduled_s']:5.1f} s, "
              f"bez ograniczenia {row['unconstrained_time_s']:5.1f} s, wymaga {speed}")
    if report["infeasible"]:
        print(f"[KOPERTA] UWAGA: {report['infeasible']} odcinków nie mieści się w rozkładzie "
              f"nawet przy {report['search_ceiling_kmh']:.0f} km/h — model jest za wolny "
              "albo odległość albo czas są złe")
    print(f"[KOPERTA] dolne ograniczenie prędkości liniowej dla sieci: "
          f"{report['network_min_top_speed_kmh']} km/h "
          f"(wiąże {report['binding_segment']['from_name']} → "
          f"{report['binding_segment']['to_name']})" if report["binding_segment"] else
          "[KOPERTA] brak odcinka wiążącego")
    print(f"[KOPERTA] zapisano {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
