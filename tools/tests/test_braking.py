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


# --- co przeżywało mutację ------------------------------------------------------


def test_braking_all_axles_fraction_is_pinned_to_one():
    """Cała konkluzja T-311 stoi na tym, że to jest JEDYNKA.

    Zmierzone 02.09.2026 audytem mutacyjnym: `ALL_AXLES_BRAKED_MASS_FRACTION`
    1,0 -> 0,5 przechodziło przez całą suitę. Testy liczyły
    `required_braked_fraction` z wklejoną literalnie jedynką, więc stała była
    wolna. Jest opisana w kodzie jako **górny kres** udziału osi hamowanych —
    zdanie „na mokrej szynie hamowanie awaryjne jest nieosiągalne przy każdym
    układzie osi" znaczy dokładnie tyle, że nawet przy f = 1 sufit nie wystarcza.
    """
    assert B.ALL_AXLES_BRAKED_MASS_FRACTION == 1.0
    assert B.ALL_AXLES_BRAKED_MASS_FRACTION >= CFG["powered_fraction"], \
        "wariant wszystkich osi nie może być słabszy od wariantu samych osi napędnych"


def test_braking_adhesion_table_verdicts_are_asserted_not_only_printed():
    """`service_ok` i `emergency_ok` z tablicy nie były sprawdzane przez nic.

    Zmierzone: odwrócenie porównania (`>=` na `<`) w obu werdyktach przechodziło —
    trafiają tylko do wydruku raportu. To one niosą główny wynik T-311.
    """
    rows = {(row["rail"], row["variant"]): row for row in B.adhesion_table(CFG)}
    assert len(rows) == 4, sorted(rows)

    for key, row in rows.items():
        assert row["service_ok"] == (row["ceiling_mps2"] >= CFG["service"]), key
        assert row["emergency_ok"] == (row["ceiling_mps2"] >= CFG["emergency"]), key
        if row["emergency_ok"]:
            assert row["service_ok"], f"{key}: awaryjne osiągalne, a służbowe nie"

    wet_all = rows[("wet", "all-axles")]
    assert wet_all["fraction"] == B.ALL_AXLES_BRAKED_MASS_FRACTION
    assert wet_all["emergency_ok"] is False, \
        "mokra szyna i wszystkie osie: hamowanie awaryjne ma być NIEosiągalne (T-311)"
    assert wet_all["service_ok"] is True, \
        "mokra szyna i wszystkie osie: hamowanie służbowe ma być osiągalne"

    dry_powered = rows[("dry", "powered-axles-only")]
    assert dry_powered["emergency_ok"] is True, \
        "sucha szyna i same osie napędne: awaryjne ma być osiągalne"
    wet_powered = rows[("wet", "powered-axles-only")]
    assert wet_powered["service_ok"] is False, \
        "mokra szyna i same osie napędne: nawet służbowe ma być nieosiągalne"


def test_braking_simulation_returns_time_and_steps_that_agree_with_the_distance():
    """`sim_brake` zwraca cztery liczby, a testy brały tylko drogę.

    Zmierzone: usunięcie warunku `v > v_target` z pętli (czyli hamowanie przez cały
    limit czasu, także po zatrzymaniu) przechodziło, bo czas i liczba kroków nie
    były sprawdzane nigdzie.
    """
    dt = 1.0 / 120.0
    v0 = 80.0 / 3.6
    distance, seconds, steps, _work = B.sim_brake(v0, CFG["service"], CFG, None, dt=dt)

    assert steps == round(seconds / dt), (steps, seconds)
    # Pętla kończy się na zatrzymaniu, a nie na limicie czasu: przy opóźnieniu
    # służbowym i zrywie z rejestru zatrzymanie z 80 km/h trwa rzędu 20–30 s,
    # więc kroków ma być rzędu tysięcy, a nie tyle, ile mieści się w limicie 120 s.
    limit_s = 120.0   # domyślny limit `sim_brake`
    assert 0 < steps < int(limit_s / dt), (steps, limit_s)
    assert 10.0 < seconds < 60.0, seconds
    # Droga musi zgadzać się z sumą v*dt po tych krokach — inaczej któraś z tych
    # trzech liczb pochodzi z innego przebiegu niż pozostałe.
    assert 0.0 < distance < v0 * seconds, (distance, v0 * seconds)
    assert distance > 0.5 * v0 * seconds, (distance, v0 * seconds)


def test_braking_integration_stops_after_exactly_the_declared_number_of_steps():
    """Limit kroków `sim_brake` jest bramką przeciw zawieszeniu i musi być pilnowany.

    Zmierzone 03.09.2026 audytem mutacyjnym: `n < max_steps` -> `n <= max_steps`
    przechodziło przez całą suitę. Każdy dotychczasowy test zadaje opóźnienie, przy
    którym pociąg staje długo przed limitem, więc licznik kroków nigdy nie dochodził
    do granicy i obie wersje warunku dawały to samo. Hamulec zadany jako 0 m/s² nie
    zatrzymuje pociągu nigdy — dopiero wtedy `max_steps` o czymkolwiek decyduje,
    a jeden krok za dużo to 0,185 m drogi doliczonej po zakończeniu przebiegu.

    W granicę trafiamy DOKŁADNIE i bez sztuczek: licznik kroków jest liczbą całkowitą,
    więc `n == max_steps` to równość int, bez marginesu zmiennoprzecinkowego. Gdyby
    granicą była tu liczba sekund, test „na granicy" musiałby ominąć pułapkę
    `(t + eps) - t != eps` — z liczbą kroków ten problem nie istnieje.
    """
    dt = 1.0 / 120.0
    v0 = 80.0 / 3.6
    for limit_s in (0.5, 1.0, 120.0):
        distance, seconds, steps, work = B.sim_brake(v0, 0.0, CFG, None,
                                                     dt=dt, limit_s=limit_s)
        assert steps == int(limit_s / dt), (limit_s, steps, int(limit_s / dt))
        assert seconds == steps * dt, (seconds, steps)
        # Zerowy hamulec nie zmienia prędkości, więc droga to dokładnie v0 * czas.
        assert abs(distance - v0 * steps * dt) < 1e-8, (limit_s, distance)
        # Opory wyłączone (`c_env is None`), więc praca oporów ma być zerem.
        assert work == 0.0, work
    # Kontrola w drugą stronę: przy prawdziwym hamulcu pętla kończy się na
    # zatrzymaniu, WYRAŹNIE przed limitem — inaczej powyższe mierzyłoby co innego.
    _s, _t, steps, _w = B.sim_brake(v0, CFG["service"], CFG, None, dt=dt, limit_s=120.0)
    assert steps < int(120.0 / dt) // 4, steps


def test_braking_adhesion_verdict_is_inclusive_at_the_exact_ceiling():
    """Werdykt tablicy ma znaczyć „sufit WYSTARCZA", czyli `>=`, a nie `>`.

    Zmierzone 03.09.2026: `>=` -> `>` w `service_ok` i w `emergency_ok` przeżywało,
    mimo że `test_braking_adhesion_table_verdicts_are_asserted_not_only_printed` oba
    te pola sprawdza. Powód jest prosty i pouczający: dla czterech wierszy liczonych
    z rejestru sufit NIGDY nie jest dokładnie równy zadaniu, a poza równością `>` i
    `>=` są nieodróżnialne. Bramka bez wejścia na granicy nie bramkuje granicy.

    W granicę trafiamy DOKŁADNIE, bo zadanie hamowania w podstawionej konfiguracji
    jest WYLICZONE tą samą funkcją, z tych samych argumentów, co sufit w tablicy —
    dwie identyczne operacje zmiennoprzecinkowe dają identyczny bit. Ta droga jest
    tu jedyna sensowna: gdybyśmy próbowali „stanąć obok granicy" epsilonem, trafiliby-
    śmy w liczbę, która granicą nie jest, bo `abs((x + eps) - x)` nie jest `eps`.

    Rejestr pozostaje nietknięty — podstawiany jest słownik `cfg`, nie plik danych.
    """
    exact = B.adhesion_ceiling_mps2(CFG["mu_dry"], B.ALL_AXLES_BRAKED_MASS_FRACTION,
                                    CFG["lam"])
    for key, verdict in (("service", "service_ok"), ("emergency", "emergency_ok")):
        tuned = dict(CFG)
        tuned[key] = exact
        row = next(r for r in B.adhesion_table(tuned)
                   if (r["rail"], r["variant"]) == ("dry", "all-axles"))
        assert row["ceiling_mps2"] == exact, (key, row["ceiling_mps2"], exact)
        assert row[verdict] is True, (
            f"{key}: sufit przyczepnościowy równy CO DO BITU zadanemu opóźnieniu ma "
            "wystarczać — werdykt musi być `>=`, nie `>`")
    # Kontrola w drugą stronę: o jeden bit poniżej sufitu werdykt ma być odmowny,
    # inaczej test przechodziłby także dla `>=` zamienionego na cokolwiek prawdziwego.
    tuned = dict(CFG)
    tuned["service"] = math.nextafter(exact, math.inf)
    row = next(r for r in B.adhesion_table(tuned)
               if (r["rail"], r["variant"]) == ("dry", "all-axles"))
    assert row["service_ok"] is False, row["ceiling_mps2"]


# --- wypis referencyjny `report()` ------------------------------------------------
#
# 6.B10 z kolejki: `report()` nie było wykonywane PRZEZ NIC. Znalezisko pochodzi
# z `reports/mutation-triage-fizyka.md` §6: „Funkcja drukuje trzy tablice referencyjne
# T-311 i mogłaby przestać się składać bez skutku dla CI. To jest osobne zadanie, nie
# triaż." Sprawdzone ponownie przed napisaniem tych testów: jedynym wołającym był blok
# `__main__` w wierszu 313 `tools/physics/braking.py`, a `grep -rn "report()" tools/`
# nie pokazywał ani jednego pliku z `tools/tests/` ani żadnego `tools/ci/*.sh`.

T311_REPORT = os.path.join(ROOT, "reports", "T-311-braking.md")

#: Nagłówki trzech tablic, które `report()` ma wypisać — CAŁE WIERSZE, nie fragmenty.
#: Trzy, nie cztery: „PROGI KRYTYCZNE" jest listą progów, nie tablicą, i jego pilnuje
#: osobna asercja niżej.
#:
#: **Dlaczego cały wiersz, a nie sam napis.** Pierwsza wersja tego testu sprawdzała
#: `"DROGA HAMOWANIA" in text` i została obalona kontrolą negatywną wykonaną
#: 05.09.2026: podmiana nagłówka w `braking.py` na `DROGA HAMOWANIA_MUTANT`
#: przechodziła OBA testy, bo napis nadal się zawierał, a `startswith` w parserze
#: wierszy nadal trafiał. Zawieranie się nie odróżnia nagłówka od nagłówka z ogonem.
#:
#: Te trzy wiersze są umową testu z wypisem, a nie cytatem z dokumentu: sprawdzone
#: gremem po `reports/` i `docs/`, **żaden raport nie cytuje ich dosłownie** —
#: cytowana jest tablica liczb z §4 `reports/T-311-braking.md` i tę pilnuje osobno
#: `test_report_distance_table_matches_the_reference_table_it_claims_to_print`.
REPORT_TABLES = (
    "SUFIT PRZYCZEPNOSCIOWY (design_assumption: udzial osi hamowanych)",
    "DROGA HAMOWANIA, hamulec sluzbowy, krok 1/120 s",
    "SOLVER PUNKTU HAMOWANIA (bez oporow, z ograniczeniem zrywu)",
)

#: Nagłówek tablicy drogi hamowania, po którym parser wierszy zaczyna czytać.
DISTANCE_TABLE_HEAD = REPORT_TABLES[1]


def report_text():
    """Wypis `report()` przechwycony ze standardowego wyjścia."""
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        B.report()
    return buffer.getvalue()


def missing_tables(text):
    """Których z trzech tablic nie ma w wypisie — pusta lista znaczy komplet.

    Porównanie do CAŁEGO wiersza, nie `in text`: nagłówek z doklejonym ogonem jest
    innym nagłówkiem, a wersja na zawieranie się przepuszczała go bez słowa.
    """
    lines = set(text.splitlines())
    return [head for head in REPORT_TABLES if head not in lines]


def printed_distance_rows(text):
    """Wiersze tablicy „DROGA HAMOWANIA" z wypisu, jako krotki dziewięciu liczb.

    Wiersz nagłówka kolumn ma dokładnie tyle samo pól co wiersz danych (dziewięć),
    więc odsiewa go pierwsza kolumna: `v0[km/h]` nie jest liczbą, a `30` jest.
    """
    rows = []
    inside = False
    for line in text.splitlines():
        if line == DISTANCE_TABLE_HEAD:
            inside = True
            continue
        if not inside:
            continue
        if not line.strip():
            break
        parts = line.split()
        if len(parts) != 9 or not parts[0].replace(".", "", 1).isdigit():
            continue
        rows.append(tuple(float(part) for part in parts))
    return rows


def reference_distance_rows():
    """Ta sama tablica, ale z `reports/T-311-braking.md` §4 — źródła, nie z kodu.

    Ostatnia kolumna raportu niesie DWIE liczby („tunel / pow."), więc krotka ma
    dziewięć pól przy ośmiu komórkach. Gwiazdki pogrubienia z wiersza 80 km/h idą
    precz przed parsowaniem, przecinek dziesiętny zamienia się na kropkę.
    """
    with open(T311_REPORT, encoding="utf-8") as handle:
        text = handle.read()
    section = text.split("## 4. Droga hamowania z oporami")[1].split("\n### ")[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().replace("**", "") for cell in line.strip("|").split("|")]
        if len(cells) != 8:
            continue
        first = cells[0].replace(",", ".")
        if not first.replace(".", "", 1).isdigit():
            continue
        head = [float(cell.replace(",", ".")) for cell in cells[:7]]
        tail = [float(part.strip().replace(",", ".")) for part in cells[7].split("/")]
        rows.append(tuple(head + tail))
    return rows


def distance_mismatches(text, reference=None):
    """Rozjazdy wypisu wobec tablicy referencyjnej — pusta lista znaczy zgodność."""
    printed = printed_distance_rows(text)
    expected = reference_distance_rows() if reference is None else reference
    if len(printed) != len(expected):
        return [f"wypis ma {len(printed)} wierszy, raport {len(expected)}"]
    problems = []
    for row, want in zip(printed, expected):
        for column, (got, expect) in enumerate(zip(row, want)):
            if got != expect:
                problems.append(
                    f"v0={row[0]:.0f} km/h, kolumna {column}: wypis {got}, raport {expect}")
    return problems


def test_report_is_actually_executed_and_prints_every_reference_table():
    """`report()` wykonuje się i drukuje komplet — do 05.09.2026 nie wołał go nikt.

    To jest cała treść pozycji 6.B10: funkcja mogła przestać się składać
    (`NameError`, zła liczba argumentów `_fmt`, literówka w kluczu słownika)
    i **żadna bramka by tego nie zauważyła**, bo jedynym wołającym był
    `if __name__ == "__main__"`. Test wywołuje ją naprawdę, więc każdy taki błąd
    kończy się wyjątkiem tutaj, a nie ciszą.
    """
    text = report_text()
    assert not missing_tables(text), missing_tables(text)
    # „PROGI KRYTYCZNE" nie jest tablicą, ale jest częścią wypisu i ma tu być.
    assert "PROGI KRYTYCZNE" in text
    # Wypis ma nieść liczby, nie same nagłówki: sześć wierszy drogi hamowania,
    # osiem wierszy sufitu (cztery warianty × dwie szyny) i pięć wierszy solvera.
    assert len(printed_distance_rows(text)) == len(B.REFERENCE_SPEEDS_KMH), text
    assert len(B.adhesion_table(CFG)) >= 4, "tablica sufitu zrobiła się pusta"
    assert text.count("s = ") >= 5, text


def test_report_distance_table_matches_the_reference_table_it_claims_to_print():
    """Wypis kontra `reports/T-311-braking.md` §4 — liczba w liczbę, bez tolerancji.

    Porównanie jest DOKŁADNE i to nie jest przeoczenie: obie strony niosą trzy
    miejsca po przecinku, więc parsowanie daje ten sam float. Gdyby tu stała
    tolerancja, test przepuszczałby dokładnie tę zmianę, przed którą stoi —
    ciche przesunięcie liczby w modelu, którego raport już nie opisuje.

    Kierunek jest zamierzony: wypis jest sprawdzany WOBEC RAPORTU, bo to raport
    jest tablicą referencyjną T-311, na którą powołuje się `docs/02-simulation.md`
    („Tablice referencyjne: `reports/T-311-braking.md`"). Rozjazd znaczy więc albo
    zmianę modelu bez aktualizacji raportu, albo odwrotnie — i w obie strony jest
    to ta sama usterka.
    """
    reference = reference_distance_rows()
    assert len(reference) == 6, (
        f"parser wyciągnął {len(reference)} wierszy z §4 raportu — tablica ma sześć "
        "prędkości (30…80 km/h); pusta lista znaczy, że przestał trafiać w sekcję")
    assert not distance_mismatches(report_text(), reference), \
        distance_mismatches(report_text(), reference)


def test_the_report_check_catches_a_table_that_stopped_being_printed():
    """Kontrola negatywna wykonana: bramka bez tego testu byłaby zielona zawsze.

    Trzy mutacje na wypisie i jedna na liczbie. Każda musi zostać zgłoszona
    Z NAZWĄ, żeby komunikat mówił, co przestało się drukować — a nie „coś nie gra".
    """
    text = report_text()
    assert not missing_tables(text), "punkt wyjścia nie jest czysty"

    # 1. Każda z trzech tablic po kolei znika z wypisu.
    for head in REPORT_TABLES:
        okrojony = text.replace(head, "")
        assert okrojony != text, f"mutacja {head} nie weszła — kontrola nic nie mierzy"
        assert missing_tables(okrojony) == [head], missing_tables(okrojony)

    # 2. Jedna liczba przesunięta o ostatnią cyfrę — tyle, ile znaczy 1 mm drogi.
    podmieniony = text.replace("233.723", "233.724")
    assert podmieniony != text, "mutacja liczby nie weszła"
    problems = distance_mismatches(podmieniony)
    assert len(problems) == 1, problems
    assert "v0=80" in problems[0] and "233.724" in problems[0], problems[0]

    # 3. Wiersz usunięty w całości — wypis krótszy od tablicy referencyjnej.
    bez_wiersza = "\n".join(line for line in text.splitlines()
                            if not line.strip().startswith("80 "))
    assert bez_wiersza != text, "mutacja wiersza nie weszła"
    assert distance_mismatches(bez_wiersza), "brak wiersza przeszedł niezauważony"

    # 4. Kontrola w drugą stronę: parser czyta z raportu, nie z kodu. Podstawiona
    #    tablica referencyjna o innej liczbie musi dać rozjazd na czystym wypisie.
    podmieniona_referencja = list(reference_distance_rows())
    zepsuty = list(podmieniona_referencja[0])
    zepsuty[1] += 0.001
    podmieniona_referencja[0] = tuple(zepsuty)
    assert distance_mismatches(text, podmieniona_referencja), (
        "porównanie ignoruje tablicę referencyjną — czytałoby wtedy samo siebie")
