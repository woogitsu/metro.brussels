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


#: Tablica referencyjna, w której stoi wiersz o przyspieszeniu rozruchu.
DOK_SYMULACJI = os.path.join(ROOT, "docs", "02-simulation.md")

#: Przyspieszenie rozruchu ZMIERZONE z modelu 10.09.2026, po jednym na obciążenie.
#: Liczby są tu po to, żeby zmiana MODELU dała inny komunikat niż rozjazd modelu
#: z opisem — pole „Skończone, gdy" pozycji 6.D86 żąda, żeby bramka umiała je
#: odróżnić. Bez tej pary jedna asercja mówiłaby „dokument się nie zgadza" także
#: wtedy, gdy to model się zmienił, a dokument został.
ROZRUCH_Z_MODELU = {"AW0": 1.342044, "AW2": 1.024782}


def przyspieszenie_rozruchu(load):
    """`a(0) = (F0 − Davis(0)) / (m · 1,08)` — liczone z tego samego modelu, co gra.

    Nie z osobnego wzoru przepisanego do testu: siła i opory idą przez
    `reference.traction_N` i `reference.davis_N`, więc zmiana modelu rusza tę liczbę.
    Mnożnik 1,08 to masa efektywna, ta sama, której używa `sim_accel`.
    """
    masa = R.MASS[load]
    return (R.traction_N(0.0, masa) - R.davis_N(masa, 0.0)) / (masa * 1.08)


def rozruch_z_dokumentu():
    """`{obciążenie: wartość}` z wiersza tabeli w `docs/02-simulation.md`."""
    tekst = open(DOK_SYMULACJI, encoding="utf-8").read()
    wiersz = re.search(r"(?m)^\| przyspieszenie rozruchu[^|]*\|([^|]*)\|", tekst)
    if wiersz is None:
        return None
    return {load: float(wartosc.replace(",", "."))
            for wartosc, load in re.findall(r"([0-9]+,[0-9]+)\s*m/s²\s*(AW[02])",
                                            wiersz.group(1))}


def test_the_start_acceleration_in_the_table_is_the_one_the_model_produces():
    """Wiersz tabeli mówi to, co model naprawdę liczy — 6.D86.

    **Skąd.** Do 10.09.2026 stało tam `1,10 m/s²` ze statusem `design_model`.
    Liczba nie występowała w kodzie ani w danych pojazdu, nikt jej nie czytał,
    a w modelu nie ma obcięcia, które by ją egzekwowało — model daje **1,342**
    (AW0) i **1,025** (AW2), czyli deklarowana wartość nie była żadną z nich, tylko
    leżała między nimi.

    **Ryzyko jest przyszłe i o nie tu chodzi:** ktoś weźmie tablicę referencyjną za
    kontrakt i dopisze sufit, którego dziś nie ma — a wtedy zmieni FIZYKĘ, sądząc,
    że poprawia opis.
    """
    z_dokumentu = rozruch_z_dokumentu()
    assert z_dokumentu, (
        "wiersz o przyspieszeniu rozruchu zniknął z tabeli w `docs/02-simulation.md` "
        "albo zmienił kształt — bramka nie ma czego porównać")
    assert set(z_dokumentu) == {"AW0", "AW2"}, (
        "tabela podaje przyspieszenie dla %s, a model liczy je dla obu obciążeń"
        % sorted(z_dokumentu))

    for load, deklarowane in sorted(z_dokumentu.items()):
        policzone = przyspieszenie_rozruchu(load)
        assert abs(policzone - deklarowane) < 5e-4, (
            "tabela podaje dla %s przyspieszenie %.3f m/s², a model liczy %.6f — "
            "wiersz opisuje coś, czego model nie robi" % (load, deklarowane, policzone))


def test_the_gate_tells_a_changed_model_apart_from_a_changed_description():
    """Druga asercja, bo dwie różne rzeczy dają ten sam objaw.

    Bramka wyżej porównuje dokument z modelem i zapala się, gdy się rozjadą — ale
    nie mówi, KTÓRA strona się ruszyła. Ten test przybija stronę MODELU do liczb
    zmierzonych 10.09.2026, więc zmiana `F0_N`, mas albo współczynników Davisa
    zapala właśnie jego, z komunikatem o modelu, a nie o dokumencie.

    Tego wprost żąda pole „Skończone, gdy": „Bramka musi odróżniać zmianę modelu
    od zmiany jego opisu."
    """
    for load, oczekiwane in sorted(ROZRUCH_Z_MODELU.items()):
        policzone = przyspieszenie_rozruchu(load)
        assert abs(policzone - oczekiwane) < 1e-6, (
            "MODEL się zmienił: przyspieszenie rozruchu dla %s to dziś %.6f m/s², "
            "a 10.09.2026 było %.6f. To nie jest rozjazd z dokumentem — to inna "
            "fizyka, więc przelicz tabelę i tę stałą razem, w jednym commicie"
            % (load, policzone, oczekiwane))

    # Sufit przyczepnościowy NIE WIĄŻE i to też jest częścią tezy: gdyby zaczął,
    # przyspieszenie przestałoby wynikać z `F0` i wzór w dokumencie byłby nieprawdą.
    for load, masa in sorted(R.MASS.items()):
        adhezja = 0.25 * masa * R.V["powered_mass_fraction"] * R.G
        assert adhezja > R.V["F0_N"], (
            "dla %s sufit przyczepnościowy (%.1f kN) zszedł poniżej siły rozruchowej "
            "(%.1f kN) — to rozstrzyga o przyspieszeniu i wzór w `docs/02-simulation.md` "
            "przestał opisywać model" % (load, adhezja / 1000, R.V["F0_N"] / 1000))


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


# Uruchamialny osobno, żeby krok CI w `sim-tests.yml` był bramką, a nie wydrukiem —
# to się nie zmienia. Zmienia się DROGA (6.D25): własna pętla po `globals()` została
# zastąpiona wspólnym przebiegaczem z `test_all.py`, bo miała dokładnie tę usterkę,
# przed którą ta pozycja broni. Gdyby `globals()` przestało dawać funkcje `test_` —
# po zmianie nazwy, po przeniesieniu do klasy — pętla nie miałaby czego wykonać,
# wypisałaby „PythonReference.cs == …, co do bitu" i zwróciła **0**. Zero testów
# meldowane jako zgodność co do bitu jest gorsze od czerwonego kroku CI.
# Wspólny przebiegacz odmawia przy zerze testów (`AG.suite_verdict`) i przy okazji
# liczy asercje, czego ta pętla nie robiła.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))


def test_reference_inputs_are_pinned_including_the_ones_nothing_derives():
    """Wejścia referencji, nie tylko liczby z nich wyprowadzone.

    Test wyżej łapie każdą zmianę, która rusza którąś z 24 stałych snapshotu —
    sprawdzone mutacjami: masa AW2, współczynnik Davisa w tunelu, masy wirujące,
    opóźnienie służbowe i zryw dają teraz czerwony. Ale wejście, z którego nie
    liczy się żadna z tych stałych, byłoby wolne — tak było z `max_speed_ms`,
    dopóki nie został usunięty (#99). Ten test przypina cały słownik, żeby
    dopisanie albo przestawienie parametru wymagało decyzji.
    """
    assert R.G == 9.80665
    assert R.MASS == {"AW0": 170000.0, "AW2": 221940.0}, R.MASS
    assert R.V == {
        "b_service": 1.10,
        "b_emergency": 1.30,
        "jerk": 0.75,
        "F0_N": 248900.0,
        "installed_power_W": 2160000.0,
        "powered_mass_fraction": 4 / 6,
    }, R.V
    assert "max_speed_ms" not in R.V, (
        "prędkość maksymalna mieszka w rejestrze (data/vehicle/m7-spec.json: "
        "max_speed_kmh, design_model) i braking.py czyta ją stamtąd — kopia w kodzie "
        "referencji byłaby drugą prawdą o tej samej wielkości")
