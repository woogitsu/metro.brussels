"""Decyzje skanu luzu M7 w tunelu — czysty Python, bez Blendera.

Wydzielone z `profile_vehicle.py`, który importuje `bpy` i przez to nie daje się
zaimportować w `tools/tests/test_all.py`. Przemiatanie mutacyjne z 03.09.2026
pokazało tam 26 mutacji i 26 ocalałych — 100 %, bo nie istniała droga, którą
test mógłby je dotknąć. Trzecia taka ekstrakcja po `tunnel_manifest.py` (#142)
i `m7_report.py` (#144).

Sama geometria luzu siedzi już w `clearance_profile.py` i jest testowalna; tutaj
zostają DECYZJE wokół niej: który tor, gdzie doszlifować, co zweryfikować naiwnie,
jaki wycinek osi zamieść obwiednią i — najważniejsze — **czy wynik wolno wypuścić**.

`profile_vehicle.py` zostaje z importem GLB, budową siatki obwiedni i eksportem.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clearance as CL  # noqa: E402
import placement as PL  # noqa: E402

# Wzór na strzałkę cięciwy wobec pomiaru na siatce. Dwa różne progi, bo dwa różne
# pytania: w pozycji odniesienia porównujemy się z `place_vehicle.py` i tam wzór ma
# prawo być tylko lekko zachowawczy; w globalnym minimum chodzi o to, żeby wzór
# i siatka w ogóle mówiły o tym samym miejscu.
FORMULA_MAX_SLACK_MM = 50.0
FORMULA_GUARD_MM = 100.0
POSITION_EPS_M = 1e-9
SAMPLE_EVERY = 25


def track_offset(offsets, index):
    """Przesunięcie żądanego toru, albo odmowa z liczbami.

    Numer toru jest indeksem do listy z profilu. Poza zakresem oznacza cichy wybór
    cudzego toru albo `IndexError` w środku skanu — jedno i drugie gorsze niż odmowa.
    """
    if not 0 <= index < len(offsets):
        raise ValueError(f"profil ma {len(offsets)} torów, żądano {index}")
    return offsets[index]


def refine_positions(windows, refine_step, axis_length, train_length, already):
    """Dodatkowe pozycje czoła składu w oknach wokół dołków luzu.

    Okna są przycinane do osi: skład nie może wystawać poza jej koniec. Warunek
    `<=` z zapasem 1e-9 domyka prawy koniec okna — bez zapasu ostatnia pozycja
    wypadałaby albo nie, zależnie od tego, jak zaokrągli się suma kroków.
    """
    stop_limit = axis_length - train_length
    extra = []
    for low, high in windows:
        value = max(0.0, low)
        stop = min(high, stop_limit)
        while value <= stop + POSITION_EPS_M:
            extra.append(round(value, 6))
            value += refine_step
    return sorted(set(extra) - set(already))


def verification_sample(records, count):
    """Pozycje do przeliczenia naiwnie: NAJGORSZA plus próbki z całego zakresu.

    Najgorsza jest zawsze pierwsza i to jest cały sens — kontrola redukcji ma
    dowieść, że redukcja nie zgubiła MINIMUM. Próbkowanie samym co n-tym elementem
    trafiłoby w minimum tylko przypadkiem.
    """
    if not records or count <= 0:
        return []
    ordered = sorted(records, key=lambda r: r["clearance_m"])
    stride = max(1, len(ordered) // count)
    picked = [ordered[0]] + ordered[1:len(ordered):stride]
    return picked[:count]


def verification_entry(record, naive):
    """Porównanie pomiaru zredukowanego z pełnym przebiegiem po wszystkich wierzchołkach."""
    return {
        "start_m": round(record["start_m"], 3),
        "reduced_m": round(record["clearance_m"], 6),
        "full_m": round(naive["clearance_m"], 6),
        "delta_mm": round(abs(record["clearance_m"] - naive["clearance_m"]) * 1000.0, 4),
        "same_object": record["object"] == naive["object"],
    }


def swept_range(centre, half_range, override_from, override_to, axis_length):
    """Wycinek osi do zamiecenia obwiednią, przycięty do osi.

    Domyślnie wokół globalnego minimum, bo tam obwiednia jest interesująca.
    Jawne `--swept-from/--swept-to` mają pierwszeństwo, ale i tak są przycinane —
    zakres poza osią dałby pustą obwiednię z zerowym kodem wyjścia.
    """
    low = override_from if override_from is not None else centre - half_range
    high = override_to if override_to is not None else centre + half_range
    return max(0.0, low), min(axis_length, high)


def contributing_starts(records, train_length, low, high):
    """Pozycje czoła, przy których JAKAKOLWIEK część składu leży w wycinku.

    Warunek jest po obu stronach nieostry, bo skład stojący dokładnie krawędzią
    na granicy wycinka nadal do niego wchodzi — pominięcie go zrobiłoby dziurę
    w obwiedni dokładnie na styku.
    """
    return [r["start_m"] for r in records
            if r["start_m"] <= high and r["start_m"] + train_length >= low]


def keep_sample(index, start, worst_start):
    """Czy zachować próbkę do kontroli zawierania się w obwiedni.

    Co 25. pozycja plus ZAWSZE ta najgorsza. Bez tego drugiego warunku kontrola
    mogłaby przejść, nie oglądając ani razu miejsca, w którym luz jest najmniejszy.
    """
    return index % SAMPLE_EVERY == 0 or abs(start - worst_start) < POSITION_EPS_M


def in_range_clearances(records, low, high):
    """Luzy zmierzone w wycinku objętym obwiednią — po chainage, nie po pozycji czoła."""
    return [r["clearance_m"] for r in records if low <= r["chainage_m"] <= high]


def static_wall_clearance(ring, offset, spec_width_m):
    """Luz do ŚCIANY na prostej dla danego toru — inna wielkość niż `profiles.min_clearance`.

    `min_clearance` inflatuje skrajnię symetrycznie i bywa wiązane przez ścięcie naroża
    stropu; tu chodzi o odległość boku pudła od ściany na torze +/- offset.
    """
    return min(PL.distance_to_boundary(ring, offset + dx, 1.0)
               for dx in (-spec_width_m / 2.0, spec_width_m / 2.0))


def formula_prediction(chord_m, radius_m, static_wall_m, measured_m, label):
    """Przewidywany luz ze wzoru na strzałkę cięciwy wobec luzu zmierzonego na siatce.

    Cięciwa jest RZECZYWISTA, z bryły, w której wypadło minimum. Nominalny podział 94/6
    daje 15,667 m zamiast 14,567 m i przewiduje luz mniejszy o ~52 mm; kontrola musi
    porównywać tę samą wielkość, inaczej mierzy własną niespójność
    (`reports/M7-in-tunnel.md` §3).
    """
    versine = CL.versine(chord_m, radius_m) if radius_m else 0.0
    predicted = static_wall_m - versine
    return {
        "variant": label,
        "chord_m": round(chord_m, 4),
        "radius_m": round(radius_m, 2) if radius_m else None,
        "versine_mm": round(versine * 1000.0, 1),
        "static_wall_clearance_m": round(static_wall_m, 4),
        "predicted_clearance_m": round(predicted, 4),
        "measured_clearance_m": round(measured_m, 4),
        "delta_mm": round(abs(predicted - measured_m) * 1000.0, 1),
        "formula_optimistic": bool(predicted > measured_m),
    }


def compact(record):
    return {
        "start_m": round(record["start_m"], 3),
        "clearance_m": round(record["clearance_m"], 5),
        "object": record["object"],
        "bound_by": record["bound_by"],
        "chainage_m": round(record["chainage_m"], 2),
        "lateral_m": round(record["lateral_m"], 4),
        "vertical_m": round(record["vertical_m"], 4),
    }


def acceptance_problems(gaps, check_reference, check, stats, outside, min_clearance_m, wall):
    """Lista powodów, dla których tego profilu NIE wolno wypuścić. Pusta = przeszedł.

    `wall` to stała `clearance_profile.WALL` — kontrole wzoru dotyczą wyłącznie
    przypadków wiązanych ŚCIANĄ, bo tylko dla nich wzór na strzałkę cięciwy w ogóle
    coś przewiduje. Gdy minimum wiąże strop albo naroże, porównanie z tym wzorem
    mierzyłoby dwie różne wielkości.

    Wzór OPTYMISTYCZNY jest problemem zawsze, niezależnie od skali: obietnica
    większego luzu, niż mierzy siatka, jest dokładnie tym rodzajem błędu, który
    kończy się kontaktem. Wzór zachowawczy jest problemem dopiero powyżej progu.
    """
    problems = list(gaps)
    if check_reference["bound_by"] == wall:
        if check_reference["formula_optimistic"]:
            problems.append(f"w pozycji odniesienia wzór OBIECUJE "
                            f"{check_reference['delta_mm']:.1f} mm więcej luzu, niż mierzy siatka")
        elif check_reference["delta_mm"] > FORMULA_MAX_SLACK_MM:
            problems.append(f"w pozycji odniesienia wzór jest zachowawczy o "
                            f"{check_reference['delta_mm']:.1f} mm > {FORMULA_MAX_SLACK_MM} mm")
    if check["bound_by"] == wall and check["delta_mm"] > FORMULA_GUARD_MM:
        problems.append(f"w globalnym minimum wzór i siatka rozjeżdżają się o "
                        f"{check['delta_mm']:.1f} mm > {FORMULA_GUARD_MM} mm")
    if stats["with_refinement"]["negative_positions"]:
        problems.append(f"{stats['with_refinement']['negative_positions']} pozycji z UJEMNYM "
                        "luzem — pojazd wchodzi w obrys tunelu")
    if outside:
        problems.append(f"{outside} wierzchołków pojazdu poza zamiataną obwiednią")
    if (min_clearance_m is not None
            and stats["with_refinement"]["min_clearance_m"] < min_clearance_m):
        problems.append(f"minimum {stats['with_refinement']['min_clearance_m']:.4f} m poniżej "
                        f"progu {min_clearance_m:.4f} m")
    return problems
