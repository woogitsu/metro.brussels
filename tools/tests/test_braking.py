#!/usr/bin/env python3
"""Testy referencji hamowania (T-311).

Ta sama rola, co testy referencji T-310 w `test_all.py`: pilnują, żeby liczby
z `tools/physics/braking.py` nie zmieniły się po cichu, i żeby żadne założenie
bez źródła nie weszło do kodu bez wiersza w `docs/21-measured-vs-assumed.md`.

Każdą liczbę, którą da się policzyć dwiema drogami, testy liczą dwiema drogami:
wzór zamknięty kontra całkowanie krokiem stałym, wzór na próg krytyczny kontra
skanowanie udziału osi, droga hamowania kontra bilans energii.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

import braking as B  # noqa: E402

AUDIT = os.path.join(ROOT, "docs", "21-measured-vs-assumed.md")
CFG = B.params()


def _audit_text():
    with open(AUDIT, encoding="utf-8") as handle:
        return handle.read()


# --- audyt założeń --------------------------------------------------------------


def test_braking_assumptions_are_all_listed_in_the_audit_document():
    text = _audit_text()
    missing = [name for name in B.BRAKING_ASSUMPTIONS if name not in text]
    assert not missing, f"zalozenia hamowania bez wpisu w audycie: {missing}"


def test_audit_states_that_ed_versus_pneumatic_split_is_not_modelled():
    text = _audit_text()
    assert "elektrodynamicznego" in text
    assert "krzywych bezpieczeństwa" in text


def test_braked_mass_fraction_has_no_entry_in_the_m7_registry():
    """Rejestr jest tylko do odczytu i nie ma prawa dostać wymyslonych parametrow."""
    raw = open(B.REGISTRY, encoding="utf-8").read().lower()
    for forbidden in ("braked_mass_fraction", "electrodynamic", "brake_blend", "safety_curve"):
        assert forbidden not in raw, forbidden


def test_braking_parameters_all_come_from_the_registry_with_design_model_status():
    """`params()` sam sprawdza status; test pilnuje, ze zadnego nie pominieto."""
    for key in ("service", "emergency", "jerk", "lam", "mu_dry", "mu_wet"):
        assert key in CFG and CFG[key] > 0.0, key
    assert CFG["service"] == 1.10 and CFG["emergency"] == 1.30 and CFG["jerk"] == 0.75


# --- sufit przyczepnościowy -----------------------------------------------------


def test_adhesion_ceiling_does_not_depend_on_train_mass():
    mu, frac = CFG["mu_dry"], 1.0
    ceiling = B.adhesion_ceiling_mps2(mu, frac, CFG["lam"])
    for mass in (CFG["aw0_kg"], CFG["aw2_kg"]):
        from_force = B.max_brake_force_n(mass, mu, frac) / (mass * CFG["lam"])
        assert math.isclose(from_force, ceiling, rel_tol=1e-15, abs_tol=0.0), mass


def test_emergency_braking_on_wet_rail_is_unreachable_with_every_axle_braked():
    """Glowny wynik T-311: f_min > 1, wiec zadna liczba osi tego nie zalatwia."""
    f_req = B.required_braked_fraction(CFG["emergency"], CFG["mu_wet"], CFG["lam"])
    assert f_req > 1.0, f_req
    # ...i ta sama konkluzja bez wspolczynnika mas wirujacych.
    assert B.required_braked_fraction(CFG["emergency"], CFG["mu_wet"], 1.0) > 1.0
    # Sluzbowe 1,10 m/s^2 na mokrym jest osiagalne, ale dopiero powyzej 93% osi.
    f_service = B.required_braked_fraction(CFG["service"], CFG["mu_wet"], CFG["lam"])
    assert 0.93 < f_service < 0.94, f_service


def test_legacy_four_sixths_fraction_fails_service_braking_on_wet_rail():
    ceiling = B.adhesion_ceiling_mps2(CFG["mu_wet"], CFG["powered_fraction"], CFG["lam"])
    assert ceiling < CFG["service"], ceiling
    # ...ale na suchej szynie ten sam udzial osi wystarcza na hamowanie awaryjne.
    dry = B.adhesion_ceiling_mps2(CFG["mu_dry"], CFG["powered_fraction"], CFG["lam"])
    assert dry > CFG["emergency"], dry


def test_critical_fraction_matches_an_independent_scan():
    """Wzor f = b*lambda/(mu*g) kontra skanowanie udzialu osi drobnym krokiem."""
    mu, demand = CFG["mu_wet"], CFG["service"]
    analytic = B.required_braked_fraction(demand, mu, CFG["lam"])
    samples = 200000
    scanned = None
    for i in range(1, samples + 1):
        frac = i / samples
        if B.adhesion_ceiling_mps2(mu, frac, CFG["lam"]) >= demand:
            scanned = frac
            break
    assert scanned is not None
    assert abs(scanned - analytic) <= 1.0 / samples, (scanned, analytic)


def test_ceiling_and_critical_fraction_are_mutual_inverses():
    for demand in (0.4, 0.8, 1.1, 1.3):
        for mu in (CFG["mu_dry"], CFG["mu_wet"]):
            frac = B.required_braked_fraction(demand, mu, CFG["lam"])
            if frac > 1.0:
                continue
            back = B.adhesion_ceiling_mps2(mu, frac, CFG["lam"])
            assert math.isclose(back, demand, rel_tol=1e-15, abs_tol=0.0), (demand, mu)


# --- solver punktu hamowania ----------------------------------------------------


def test_closed_form_is_the_limit_of_the_stepped_model():
    """Blad ma malec liniowo z krokiem — inaczej wzor i model to dwie rozne fizyki."""
    v0 = CFG["max_speed_kmh"] / 3.6
    closed = B.braking_distance_m(v0, 0.0, CFG["service"], CFG["jerk"])
    previous = None
    for hz in (120, 1200, 12000):
        s, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, None, dt=1.0 / hz)
        error = closed - s
        assert error > 0.0, hz
        if previous is not None:
            assert abs(previous / error - 10.0) < 0.05, (hz, previous / error)
        previous = error


def test_solver_is_the_inverse_of_the_distance_formula():
    v0 = CFG["max_speed_kmh"] / 3.6
    for distance in (150.0, 200.0, 240.0, 300.0, 400.0):
        b = B.required_deceleration_mps2(v0, 0.0, distance, CFG["jerk"])
        back = B.braking_distance_m(v0, 0.0, b, CFG["jerk"])
        assert abs(back - distance) < 1e-9, (distance, back)


def test_jerk_sets_a_floor_on_braking_distance():
    """Ponizej minimum ze zrywu nie ma rozwiazania i solver mowi to wprost."""
    v0 = CFG["max_speed_kmh"] / 3.6
    minimum = B.minimum_distance_m(v0, 0.0, CFG["jerk"])
    assert 114.0 < minimum < 114.1, minimum
    assert B.required_deceleration_mps2(v0, 0.0, minimum - 1e-6, CFG["jerk"]) is None
    assert B.required_deceleration_mps2(v0, 0.0, minimum, CFG["jerk"]) is not None


def test_distance_at_the_plateau_ceiling_equals_the_ramp_only_distance():
    """Wzor zamkniety i wzor na sam zryw musza sie spotkac w punkcie progowym."""
    v0 = CFG["max_speed_kmh"] / 3.6
    ceiling = B.plateau_ceiling_mps2(v0, 0.0, CFG["jerk"])
    closed = B.braking_distance_m(v0, 0.0, ceiling, CFG["jerk"])
    ramp = B.ramp_only_distance_m(v0, 0.0, CFG["jerk"])
    assert abs(closed - ramp) < 1e-9, (closed, ramp)


def test_closed_form_reduces_to_v_squared_over_two_a_without_jerk():
    v0, v1, b = 80 / 3.6, 30 / 3.6, 1.10
    textbook = (v0 * v0 - v1 * v1) / (2.0 * b)
    assert abs(B.braking_distance_m(v0, v1, b, 75000.0) - textbook) < 1e-3


def test_braking_distance_decreases_with_deceleration():
    v0 = CFG["max_speed_kmh"] / 3.6
    ceiling = B.plateau_ceiling_mps2(v0, 0.0, CFG["jerk"])
    previous = float("inf")
    for i in range(1, 201):
        s = B.braking_distance_m(v0, 0.0, ceiling * i / 200.0, CFG["jerk"])
        assert s < previous, i
        previous = s


# --- droga hamowania z oporami ---------------------------------------------------


def test_resistance_shortens_braking_distance_and_the_tunnel_shortens_it_more():
    for row in B.distance_table(CFG):
        assert row["tunnel_m"] < row["kinematic_m"], row["start_kmh"]
        assert row["surface_m"] < row["kinematic_m"], row["start_kmh"]
        assert row["tunnel_m"] < row["surface_m"], row["start_kmh"]


def test_shortening_matches_the_energy_balance_for_every_speed():
    """Druga droga: praca oporow podzielona przez sile hamowania to te same metry."""
    for row in B.distance_table(CFG):
        assert abs(row["tunnel_shortening_m"] - row["tunnel_shortening_from_energy_m"]) < 0.02, row
        assert abs(row["surface_shortening_m"] - row["surface_shortening_from_energy_m"]) < 0.02, row


def test_davis_deceleration_does_not_depend_on_mass():
    """Davis liczy sie na tone, wiec masa skraca sie i AW0 hamuje jak AW2."""
    a = B.davis_deceleration_mps2(80 / 3.6, CFG, CFG["tunnel_c"])
    for mass in (CFG["aw0_kg"], CFG["aw2_kg"]):
        force = B.davis_kgf_per_tonne(80 / 3.6, CFG, CFG["tunnel_c"]) * (mass / 1000.0) * B.G
        assert math.isclose(force / (mass * CFG["lam"]), a, rel_tol=1e-15, abs_tol=0.0), mass


def test_service_braking_from_80_reproduces_the_measured_t400_numbers():
    """Kontrola wobec `reports/T-400-first-run.md` §3.6, gdzie te liczby juz stoja."""
    v0 = 80 / 3.6
    s_kin, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, None)
    s_tun, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, CFG["tunnel_c"])
    assert abs(s_kin - 240.479) < 1e-3, s_kin
    assert abs(s_tun - 233.723) < 1e-3, s_tun
    assert abs((s_kin - s_tun) - 6.757) < 1e-3, s_kin - s_tun


def test_downhill_braking_is_longer_and_uphill_is_shorter():
    v0 = 80 / 3.6
    level, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, CFG["tunnel_c"])
    down, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, CFG["tunnel_c"], grade_pct=-3.0)
    up, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, CFG["tunnel_c"], grade_pct=3.0)
    assert down > level > up, (down, level, up)


def test_emergency_braking_is_shorter_than_service_braking():
    v0 = 80 / 3.6
    service, _, _, _ = B.sim_brake(v0, CFG["service"], CFG, CFG["tunnel_c"])
    emergency, _, _, _ = B.sim_brake(v0, CFG["emergency"], CFG, CFG["tunnel_c"])
    assert emergency < service, (emergency, service)


def test_adhesion_ceiling_makes_wet_emergency_braking_longer_than_dry():
    """Na mokrej szynie zadanie 1,30 m/s^2 zostaje obciete, wiec droga rosnie."""
    v0 = 80 / 3.6
    frac = CFG["powered_fraction"]
    dry_rate = min(CFG["emergency"], B.adhesion_ceiling_mps2(CFG["mu_dry"], frac, CFG["lam"]))
    wet_rate = min(CFG["emergency"], B.adhesion_ceiling_mps2(CFG["mu_wet"], frac, CFG["lam"]))
    assert dry_rate == CFG["emergency"]
    assert wet_rate < CFG["emergency"]
    dry, _, _, _ = B.sim_brake(v0, dry_rate, CFG, CFG["tunnel_c"])
    wet, _, _, _ = B.sim_brake(v0, wet_rate, CFG, CFG["tunnel_c"])
    assert wet > dry + 100.0, (wet, dry)
