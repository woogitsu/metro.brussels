#!/usr/bin/env python3
"""Snapshot referencji w C# musi zgadzać się z referencją w Pythonie.

`tests/Sim.Tests/PythonReference.cs` jest ręcznie przepisaną kopią liczb
z `tools/physics/reference.py`. Rdzeń C# porównuje się z tą kopią, a kopia
z niczym — więc zmiana modelu w Pythonie mogła rozjechać obie strony i
przejść przez całe CI.

Zmierzone przed dodaniem tego testu: obcięcie mocy trakcji w `reference.py`
o 10 % przesuwa drogę rozruchu z 337,5 m na 371,3 m, a `dotnet test` nadal
daje `Passed: 252`. Krok CI o nazwie „Reference parity is still reproducible
from Python" był w tamtym momencie zwykłym `print`.

Ten test zamyka pętlę po stronie, która ma interpreter: liczy wartości
referencyjne od nowa i porównuje je ze stałymi z pliku C# **na pełnej
precyzji** — tak samo, jak zostały tam zapisane (`repr()` double).
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

import reference as R  # noqa: E402

SNAPSHOT = os.path.join(ROOT, "tests", "Sim.Tests", "PythonReference.cs")


def _constants():
    """Stałe z pliku C# jako {nazwa: wartość}. Komentarze XML są pomijane."""
    text = open(SNAPSHOT, encoding="utf-8").read()
    found = {}
    for kind, name, raw in re.findall(
            r"public const (int|long|double) ([A-Za-z0-9]+) = ([-0-9.eE+]+);", text):
        found[name] = int(raw) if kind in ("int", "long") else float(raw)
    return found


def _expected():
    steps = R.sim_accel  # skrót czytelności
    dt = 1.0 / 120.0
    accel_aw0 = steps(R.MASS["AW0"], 80)
    accel_aw2 = steps(R.MASS["AW2"], 80)
    uphill = steps(R.MASS["AW2"], 80, 3.0)
    downhill = steps(R.MASS["AW2"], 80, -3.0)
    wet = steps(R.MASS["AW0"], 80, mu=0.13)
    service = R.sim_brake(R.MASS["AW0"], 80, R.V["b_service"])
    emergency = R.sim_brake(R.MASS["AW0"], 80, R.V["b_emergency"])
    v80 = 80 / 3.6
    adhesion = lambda mass, mu: mu * mass * R.V["powered_mass_fraction"] * R.G
    return {
        "StepsPerSecond": int(round(1.0 / dt)),
        "TransitionSpeedMps": R.base_speed_ms(),
        "TransitionSpeedKmh": R.base_speed_ms() * 3.6,
        "Accel80Aw0TimeS": accel_aw0[0],
        "Accel80Aw0DistanceM": accel_aw0[1],
        "Accel80Aw0Steps": int(round(accel_aw0[0] / dt)),
        "Accel80Aw2TimeS": accel_aw2[0],
        "Accel80Aw2DistanceM": accel_aw2[1],
        "Accel80Aw2Steps": int(round(accel_aw2[0] / dt)),
        "ServiceBrake80TimeS": service[0],
        "ServiceBrake80DistanceM": service[1],
        "ServiceBrake80Steps": int(round(service[0] / dt)),
        "EmergencyBrake80TimeS": emergency[0],
        "EmergencyBrake80DistanceM": emergency[1],
        "Accel80Aw2UphillTimeS": uphill[0],
        "Accel80Aw2UphillDistanceM": uphill[1],
        "Accel80Aw2DownhillTimeS": downhill[0],
        "Accel80Aw2DownhillDistanceM": downhill[1],
        "Accel80Aw0WetTimeS": wet[0],
        "Accel80Aw0WetDistanceM": wet[1],
        "DavisTunnelAw080KmhN": R.davis_N(R.MASS["AW0"], v80, tunnel=True),
        "DavisSurfaceAw080KmhN": R.davis_N(R.MASS["AW0"], v80, tunnel=False),
        "AdhesionLimitAw0DryN": adhesion(R.MASS["AW0"], 0.25),
        "AdhesionLimitAw2WetN": adhesion(R.MASS["AW2"], 0.13),
    }


def test_reference_snapshot_covers_every_constant_in_the_csharp_file():
    """Każda stała z pliku C# musi być tu przeliczana — inaczej test cichnie."""
    missing = sorted(set(_constants()) - set(_expected()))
    assert not missing, missing


def test_reference_snapshot_matches_python_to_full_precision():
    """Rozjazd referencji Pythona ze snapshotem C# ma wywalić CI, a nie wypisać się w logu."""
    expected = _expected()
    actual = _constants()
    assert actual, "nie wyciągnięto ani jednej stałej — wzorzec przestał pasować"
    mismatched = []
    for name, want in expected.items():
        assert name in actual, name
        got = actual[name]
        if isinstance(want, int):
            if got != want:
                mismatched.append(f"{name}: C# {got} != Python {want}")
        elif repr(got) != repr(want):
            mismatched.append(f"{name}: C# {got!r} != Python {want!r}")
    assert not mismatched, mismatched


def main():
    """Uruchamialny osobno, żeby krok CI w sim-tests.yml był bramką, a nie wydrukiem."""
    failed = []
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed.append(name)
    if failed:
        print(f"\n  snapshot C# rozjechał się z tools/physics/reference.py: {failed}")
        return 1
    print("\n  PythonReference.cs == tools/physics/reference.py, co do bitu")
    return 0


if __name__ == "__main__":
    sys.exit(main())


def test_reference_inputs_are_pinned_including_the_ones_nothing_derives():
    """Wejścia referencji, nie tylko liczby z nich wyprowadzone.

    Test wyżej łapie każdą zmianę, która rusza którąś z 24 stałych snapshotu —
    sprawdzone mutacjami: masa AW2, współczynnik Davisa w tunelu, masy wirujące,
    opóźnienie służbowe i zryw dają teraz czerwony. Ale `max_speed_ms` NIE wchodzi
    do żadnej z tych stałych (wszystkie liczone są dla zadanej wprost prędkości
    80 km/h), więc jego zmiana 80 -> 40 km/h przechodziła. Ten test przypina cały
    słownik wejść, żeby dopisanie albo przestawienie parametru wymagało decyzji.

    Uwaga zauważona przy okazji: `max_speed_ms` nie jest czytane przez nic
    w repo — ani przez `reference.py`, ani przez testy, ani przez rdzeń C#.
    To martwa liczba w pliku, który jest źródłem parytetu; usunięcie albo użycie
    jej jest osobną decyzją, nie zmianą testów.
    """
    assert R.G == 9.80665
    assert R.MASS == {"AW0": 170000.0, "AW2": 221940.0}, R.MASS
    assert R.V == {
        "b_service": 1.10,
        "b_emergency": 1.30,
        "jerk": 0.75,
        "max_speed_ms": 80 / 3.6,
        "F0_N": 248900.0,
        "installed_power_W": 2160000.0,
        "powered_mass_fraction": 4 / 6,
    }, R.V
