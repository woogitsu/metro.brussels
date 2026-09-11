#!/usr/bin/env python3
"""Referencja hamowania M7 — druga, niezależna droga do liczb z `src/Sim`.

Ta sama rola, jaką `tools/physics/reference.py` pełni dla T-310: rdzeń w C# ma
odtwarzać te liczby, a nie liczby podobne. Moduł jest osobny, bo `reference.py`
jest zamrożoną referencją parytetu T-310 i nie ma powodu jej ruszać.

Wszystkie parametry pochodzą z `data/vehicle/m7-spec.json` — plik jest czytany,
nie przepisywany, więc nie ma tu ani jednej wklejonej liczby o pojeździe.
Wyjątkiem jest udział osi hamowanych, którego **w rejestrze nie ma** i którego
nie wolno wymyślić: jest jawnym parametrem o dwóch wariantach skrajnych,
wypisanym w `BRAKING_ASSUMPTIONS` i w `docs/21-measured-vs-assumed.md`.

Model hamowania jest ten sam, co w `src/Sim`:

    * opóźnienie narasta zrywem `j` od zera do zadanego `b`;
    * opory Davisa `r = a + b_d·v + c_d·c·v²` [kgf/t] pomagają hamować;
    * siła hamulca działa na masę efektywną `m·λ`, tak samo jak w TrainController;
    * sufit przyczepnościowy `F ≤ μ·m·f·g`, czyli `b ≤ μ·f·g/λ`.
"""
import json
import math
import os

G = 9.80665
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY = os.path.join(ROOT, "data", "vehicle", "m7-spec.json")

#: Udział osi hamowanych. Brak źródła — patrz `docs/21-measured-vs-assumed.md` §7.
#: 1,0 to górny kres (wszystkie osie hamują); wariant dolny bierze `powered_mass_fraction`
#: z rejestru, gdzie sam jest `design_model` i opisany jako parametr limitu adhezji
#: dla TRAKCJI, więc przeniesienie go na hamowanie jest osobnym założeniem.
ALL_AXLES_BRAKED_MASS_FRACTION = 1.0

BRAKING_ASSUMPTIONS = {
    "AllAxlesBrakedMassFraction": (
        ALL_AXLES_BRAKED_MASS_FRACTION,
        "gorny kres udzialu osi hamowanych; brak publicznego ukladu hamulcowego M7",
    ),
    "PoweredAxlesBrakedMassFraction": (
        None,  # z rejestru: parameters.powered_mass_fraction
        "wariant dolny: hamuja tylko osie napedne; 4/6 jest design_model dla TRAKCJI",
    ),
    "BrakeForceInertiaFactor": (
        None,  # z rejestru: reference_model.effective_mass_factor
        "sila hamulca liczona od masy efektywnej m*lambda, tak samo jak TrainController",
    ),
}


def load_registry(path=REGISTRY):
    """Rejestr M7 jako słownik. Czytany, nigdy nie zapisywany (reguła 6)."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


#: Status parametru wymyślonego przez ten projekt jako założenie modelu.
STATUS_MODELU = "design_model"

#: Status wartości pochodzącej z oficjalnego źródła, z `source_id` w rejestrze.
STATUS_ZE_ZRODLA = "spec"

#: PIĘTNAŚCIE parametrów modelu hamowania: nazwa w wyniku, sekcja rejestru, klucz
#: i status, jakiego ten parametr WYMAGA. Tabela jest jedynym źródłem tej wiedzy —
#: `params` buduje z niej wynik, a bramka po niej chodzi, więc „ile ich jest"
#: i „który jakiego statusu wymaga" nie stoi w dwóch miejscach osobno.
#:
#: **Czternaście `design_model` i JEDEN `spec`** — zmierzone 10.09.2026 (6.D107).
#: `empty_mass_kg` do tego dnia był czytany BEZ ŻADNEJ kontroli statusu, jako
#: `float(par["empty_mass_kg"]["value"])`. Nie dlatego, że jego pochodzenie było
#: gorsze: w rejestrze ma `spec`, `source_id: stib_m7_2020_07_13` i notatkę „STIB
#: states approximately 170 tonnes". Przez `design()` przejść **nie mógł**, bo tamten
#: strażnik żąda `design_model` — i to jest cały powód, dla którego go ominięto.
#: Pominięcie kontroli zamiast dobrania właściwej zostawiało jednak parametr bez
#: strażnika, a brak kontroli nie zostawia śladu w żadnym wypisie.
PARAMETRY = (
    ("service", "reference_model", "service_brake_mps2", STATUS_MODELU),
    ("emergency", "reference_model", "emergency_brake_mps2", STATUS_MODELU),
    ("jerk", "reference_model", "jerk_mps3", STATUS_MODELU),
    ("lam", "reference_model", "effective_mass_factor", STATUS_MODELU),
    ("mu_dry", "reference_model", "adhesion_dry", STATUS_MODELU),
    ("mu_wet", "reference_model", "adhesion_wet", STATUS_MODELU),
    ("davis_a", "reference_model", "davis_a", STATUS_MODELU),
    ("davis_b", "reference_model", "davis_b", STATUS_MODELU),
    ("davis_c", "reference_model", "davis_c", STATUS_MODELU),
    ("tunnel_c", "reference_model", "tunnel_resistance_multiplier", STATUS_MODELU),
    ("surface_c", "reference_model", "surface_resistance_multiplier", STATUS_MODELU),
    ("powered_fraction", "parameters", "powered_mass_fraction", STATUS_MODELU),
    ("max_speed_kmh", "parameters", "max_speed_kmh", STATUS_MODELU),
    ("aw0_kg", "parameters", "empty_mass_kg", STATUS_ZE_ZRODLA),
    ("aw2_kg", "reference_model", "aw2_model_mass_kg", STATUS_MODELU),
)


def o_statusie(container, key, oczekiwany):
    """Wartość parametru, ale tylko gdy jego status jest tym, którego się spodziewamy.

    6.D94: ODMOWA, NIE `assert`. Pod `python3 -O` ten warunek znikał w całości,
    a jest to kontrola POCHODZENIA liczby: parametr o dowolnym innym statusie
    wchodziłby wtedy do modelu hamowania bez śladu. `ValueError` z tym samym
    uzasadnieniem, co w `m7_layout.py:81`, gdzie ta sama klasa kontroli
    (status wymiaru) od początku była odmową, a nie asercją.

    6.D107: oczekiwany status jest ARGUMENTEM, a nie stałą wpisaną w warunek.
    Czternaście parametrów wymaga `design_model`, jeden — `spec`, i różnica nie
    jest luką: wartość ze źródła ma pochodzenie MOCNIEJSZE, nie słabsze. Strażnik
    z wpisaną na sztywno jedną nazwą statusu zmuszał do wyboru między odrzuceniem
    dobrej liczby a pominięciem kontroli; ominięto kontrolę.
    """
    rec = container[key]
    if rec["status"] != oczekiwany:
        raise ValueError(
            f"{key} ma status {rec['status']!r}, a model hamowania wolno budować "
            f"z tego parametru wyłącznie przy statusie {oczekiwany!r}")
    return float(rec["value"])


#: Klucz rejestru, którym wartość mówi „to jest przybliżenie, nie pomiar".
#:
#: **Zmierzone 11.09.2026 (6.D124): w całym `data/` niesie go DOKŁADNIE JEDNA
#: wartość** — `parameters.empty_mass_kg`, 170 000 kg, z notatką „STIB states
#: approximately 170 tonnes; retain approximation explicitly". Skan po wszystkich
#: `data/**/*.json` nie znalazł ani drugiej.
#:
#: **Jeden to liczba o REJESTRZE, nie o danych** — i to jest najważniejsze zdanie
#: tej stałej. Przybliżeń w projekcie jest więcej, tylko mówią o sobie inaczej:
#: `data/network/station-depths.csv` ma kolumnę `confidence`, a w niej **trzy**
#: wiersze `estimated` (De Brouckère, Parc, Arts-Loi — te same, które 6.D120
#: wpuściło do geometrii). Tamte nie wchodzą do modelu jazdy i mają własny język,
#: więc ten licznik ich nie widzi i widzieć nie ma.
KLUCZ_PRZYBLIZENIA = "approximate"


def przyblizone_wpisy(registry=None):
    """`[(sciezka, wartosc, notatka)]` dla WSZYSTKICH wpisów rejestru z flagą.

    **Ścieżką rejestru, nie nazwą modelu — i to nie jest kosmetyka.** Wypis tej
    listy jest porównywany `diff`em z wypisem rdzenia C# (krok „Sim.Runner braking
    kontra referencja" w `sim-tests.yml`), a rdzeń czyta ten sam plik i zna wpisy
    po ścieżkach `sekcja.klucz`. Nazwy pythonowe (`aw0_kg`) istnieją wyłącznie po
    tej stronie, więc wypisanie ich zmusiłoby rdzeń do trzymania drugiej kopii
    tablicy nazw — czyli dokładnie tego, czego ta pozycja unika gdzie indziej.

    Zmierzone 11.09.2026: pierwsza wersja wypisywała `aw0_kg = empty_mass_kg` i to
    **wywróciło job `sim`** (`diff` pokazał dwa wiersze obecne tylko po stronie
    Pythona). Bramka zadziałała dokładnie tak, jak ma działać.
    """
    reg = registry if registry is not None else load_registry()
    znalezione = []
    for sekcja in ("parameters", "reference_model"):
        for klucz, rec in sorted(reg.get(sekcja, {}).items()):
            if isinstance(rec, dict) and rec.get(KLUCZ_PRZYBLIZENIA) is True:
                znalezione.append((f"{sekcja}.{klucz}", float(rec["value"]),
                                   rec.get("notes") or ""))
    return znalezione


def parametry_przyblizone(registry=None):
    """`[(nazwa, klucz, wartosc, notatka)]` dla parametrów modelu z flagą przybliżenia.

    Liczone **z rejestru**, po tej samej tabeli `PARAMETRY`, z której `params`
    buduje model. Własna lista nazw byłaby drugą kopią wiedzy „który parametr jest
    przybliżony" i rozjechałaby się przy pierwszej zmianie w `data/` — dokładnie
    tak, jak rozjechałby się licznik wpisany tu liczbą.

    Zwraca listę, a nie liczbę, bo pole „Wyjście" pozycji 6.D124 żąda **wykazu**
    tych, które wchodzą do modelu, a nie samego licznika.
    """
    reg = registry if registry is not None else load_registry()
    znalezione = []
    for nazwa, sekcja, klucz, _status in PARAMETRY:
        rec = reg[sekcja][klucz]
        if rec.get(KLUCZ_PRZYBLIZENIA) is True:
            znalezione.append((nazwa, klucz, float(rec["value"]),
                               rec.get("notes") or ""))
    return znalezione


def params(registry=None):
    """Parametry modelu hamowania wyjęte z rejestru, z kontrolą statusu.

    **Wszystkie piętnaście przechodzi przez kontrolę** (6.D107); do 10.09.2026
    czternaście, bo `empty_mass_kg` był czytany wprost. Który jakiego statusu
    wymaga, mówi `PARAMETRY`.
    """
    reg = registry if registry is not None else load_registry()
    return {
        nazwa: o_statusie(reg[sekcja], klucz, status)
        for nazwa, sekcja, klucz, status in PARAMETRY
    }


# --- 1. sufit przyczepnościowy -------------------------------------------------


def adhesion_ceiling_mps2(mu, fraction, lam):
    """Sufit opóźnienia pudła: `mu*f*g/lam`. Nie zależy od masy składu."""
    return mu * fraction * G / lam


def adhesion_ceiling_rigid_mps2(mu, fraction):
    """Ten sam sufit przy zignorowaniu mas wirujących: `mu*f*g`."""
    return mu * fraction * G


def required_braked_fraction(decel, mu, lam):
    """Najmniejszy udział osi hamowanych dla zadanego opóźnienia. >1 = nieosiągalne."""
    return decel * lam / (mu * G)


def required_adhesion(decel, fraction, lam):
    """Najmniejsza przyczepność dla zadanego opóźnienia przy tym udziale osi."""
    return decel * lam / (fraction * G)


def max_brake_force_n(mass_kg, mu, fraction):
    """Największa siła hamowania przenoszalna przez styk koło-szyna."""
    return mu * mass_kg * fraction * G


# --- 2. solver punktu hamowania ------------------------------------------------


def plateau_ceiling_mps2(v0, v1, jerk):
    """Opóźnienie, powyżej którego cel wypada jeszcze w trakcie narastania hamulca."""
    return math.sqrt(2.0 * jerk * (v0 - v1))


def braking_distance_m(v0, v1, decel, jerk):
    """Droga hamowania ze wzoru zamkniętego, z ograniczeniem zrywu.

    s(b) = (v0^2 - v1^2)/(2b) + v0*b/(2j) - b^3/(24 j^2)

    Pierwszy człon to szkolne v^2/2a; dwa pozostałe są ceną zrywu i znikają przy j -> inf.
    """
    return ((v0 * v0 - v1 * v1) / (2.0 * decel)
            + v0 * decel / (2.0 * jerk)
            - decel ** 3 / (24.0 * jerk * jerk))


def braking_time_s(v0, v1, decel, jerk):
    """Czas hamowania: (v0-v1)/b + b/(2j)."""
    return (v0 - v1) / decel + decel / (2.0 * jerk)


def ramp_only_distance_m(v0, v1, jerk):
    """Droga, gdy cel wypada w trakcie narastania — nie zależy już od zadanego b."""
    tf = math.sqrt(2.0 * (v0 - v1) / jerk)
    return v0 * tf - jerk * tf ** 3 / 6.0


def minimum_distance_m(v0, v1, jerk):
    """Najkrótsza droga dopuszczona przez sam zryw, bez względu na siłę hamulca."""
    return ramp_only_distance_m(v0, v1, jerk)


def required_deceleration_mps2(v0, v1, distance, jerk, steps=200):
    """Odwrotność: jakie opóźnienie zejdzie z v0 do v1 dokładnie na zadanej drodze.

    Zwraca None, gdy droga jest krótsza niż `minimum_distance_m` — wtedy rozwiązania
    nie ma i „prawie" nie jest odpowiedzią.
    """
    ceiling = plateau_ceiling_mps2(v0, v1, jerk)
    if distance < ramp_only_distance_m(v0, v1, jerk):
        return None
    low, high = 0.0, ceiling
    for _ in range(steps):
        mid = 0.5 * (low + high)
        if mid <= low or mid >= high:
            break
        if braking_distance_m(v0, v1, mid, jerk) > distance:
            low = mid
        else:
            high = mid
    return high


# --- 3. przebieg z oporami ------------------------------------------------------


def davis_kgf_per_tonne(v_ms, cfg, c_env):
    """Opór jednostkowy w kgf/t przy prędkości w m/s."""
    v_kmh = v_ms * 3.6
    return cfg["davis_a"] + cfg["davis_b"] * v_kmh + cfg["davis_c"] * c_env * v_kmh * v_kmh


def davis_deceleration_mps2(v_ms, cfg, c_env):
    """Opóźnienie od oporów. **Nie zależy od masy** — Davis jest liczony na tonę."""
    return davis_kgf_per_tonne(v_ms, cfg, c_env) * G / (1000.0 * cfg["lam"])


def sim_brake(v0, decel, cfg, c_env=None, grade_pct=0.0, v_target=0.0, dt=1.0 / 120.0,
              limit_s=120.0):
    """Całkowanie hamowania krokiem stałym, tą samą kolejnością działań co TrainController.

    Zwraca (droga, czas, kroki, praca_oporow_na_kg_efektywny).
    `c_env = None` wyłącza opory — wtedy model jest kinematyczny jak w T-310.
    """
    v = v0
    s = 0.0
    a_brake = 0.0
    n = 0
    resistance_per_kg = 0.0
    grade_a = G * grade_pct / 100.0 / cfg["lam"]
    max_steps = int(limit_s / dt)
    while v > v_target and n < max_steps:
        a_brake = min(decel, a_brake + cfg["jerk"] * dt)
        a_res = 0.0 if c_env is None else davis_deceleration_mps2(v, cfg, c_env)
        v = max(v_target, v - (a_brake + a_res + grade_a) * dt)
        ds = v * dt
        s += ds
        resistance_per_kg += a_res * ds
        n += 1
    return s, n * dt, n, resistance_per_kg


# --- 4. tablice referencyjne ----------------------------------------------------

REFERENCE_SPEEDS_KMH = (30.0, 40.0, 50.0, 60.0, 70.0, 80.0)


def adhesion_table(cfg):
    """Sufit przyczepnościowy dla obu μ i obu wariantów udziału osi."""
    rows = []
    fractions = (("all-axles", ALL_AXLES_BRAKED_MASS_FRACTION),
                 ("powered-axles-only", cfg["powered_fraction"]))
    for rail, mu in (("dry", cfg["mu_dry"]), ("wet", cfg["mu_wet"])):
        for name, frac in fractions:
            rows.append({
                "rail": rail,
                "mu": mu,
                "variant": name,
                "fraction": frac,
                "ceiling_mps2": adhesion_ceiling_mps2(mu, frac, cfg["lam"]),
                "ceiling_rigid_mps2": adhesion_ceiling_rigid_mps2(mu, frac),
                "service_ok": adhesion_ceiling_mps2(mu, frac, cfg["lam"]) >= cfg["service"],
                "emergency_ok": adhesion_ceiling_mps2(mu, frac, cfg["lam"]) >= cfg["emergency"],
            })
    return rows


def distance_table(cfg, speeds=REFERENCE_SPEEDS_KMH, decel=None):
    """Droga hamowania: bez oporów, w tunelu i na powierzchni, dla kilku prędkości."""
    decel = cfg["service"] if decel is None else decel
    rows = []
    for kmh in speeds:
        v0 = kmh / 3.6
        s_kin, t_kin, n_kin, _ = sim_brake(v0, decel, cfg, None)
        s_tun, t_tun, _, w_tun = sim_brake(v0, decel, cfg, cfg["tunnel_c"])
        s_sur, t_sur, _, w_sur = sim_brake(v0, decel, cfg, cfg["surface_c"])
        rows.append({
            "start_kmh": kmh,
            "closed_form_m": braking_distance_m(v0, 0.0, decel, cfg["jerk"]),
            "kinematic_m": s_kin,
            "kinematic_s": t_kin,
            "kinematic_steps": n_kin,
            "tunnel_m": s_tun,
            "tunnel_s": t_tun,
            "surface_m": s_sur,
            "surface_s": t_sur,
            "tunnel_shortening_m": s_kin - s_tun,
            "surface_shortening_m": s_kin - s_sur,
            "tunnel_shortening_from_energy_m": w_tun / decel,
            "surface_shortening_from_energy_m": w_sur / decel,
        })
    return rows


def _fmt(value, digits=3):
    return f"{value:.{digits}f}"


def report(registry=None):
    """Wypis tablic referencyjnych — do wklejenia i do porównania z rdzeniem.

    `registry` istnieje po to, żeby dało się WYKONAĆ przypadek, którego dzisiejsze
    dane nie produkują: wypis przy ZERZE parametrów przybliżonych (6.D124). Bez
    niego zdanie „wiersz pada zawsze" byłoby nieodróżnialne od „wiersz pada, bo
    akurat jest co wypisać" — a przybliżony parametr jest dziś dokładnie jeden.
    """
    cfg = params(registry)
    print(f"zryw = {cfg['jerk']} m/s^3, lambda = {cfg['lam']}, "
          f"sluzbowe = {cfg['service']} m/s^2, awaryjne = {cfg['emergency']} m/s^2")
    # 6.D124: wiersz pada ZAWSZE, także przy zerze. Wypisywanie go tylko wtedy, gdy
    # jest co wypisać, robi z ciszy dwa różne zdania — „nic nie jest przybliżone"
    # i „nikt nie sprawdzał" — nieodróżnialne dla czytającego wypis.
    przyblizone = przyblizone_wpisy(registry)
    print(f"PARAMETRY PRZYBLIZONE (rejestr, {KLUCZ_PRZYBLIZENIA}: true): "
          f"{len(przyblizone)}")
    for sciezka, wartosc, notatka in przyblizone:
        print(f"  {sciezka} = {wartosc:g}" + (f"  — {notatka}" if notatka else ""))
    print()
    print("SUFIT PRZYCZEPNOSCIOWY (design_assumption: udzial osi hamowanych)")
    print("rail  mu     wariant             f       b_max     b_max_bez_lambda  1.10  1.30")
    for row in adhesion_table(cfg):
        print(f"{row['rail']:5s} {row['mu']:<6.2f} {row['variant']:<19s} "
              f"{row['fraction']:.4f}  {_fmt(row['ceiling_mps2'], 4):>8s}  "
              f"{_fmt(row['ceiling_rigid_mps2'], 4):>16s}  "
              f"{'tak' if row['service_ok'] else 'NIE':>4s}  "
              f"{'tak' if row['emergency_ok'] else 'NIE':>4s}")
    print()
    print("PROGI KRYTYCZNE")
    for decel, name in ((cfg["service"], "sluzbowe"), (cfg["emergency"], "awaryjne")):
        for rail, mu in (("dry", cfg["mu_dry"]), ("wet", cfg["mu_wet"])):
            f_req = required_braked_fraction(decel, mu, cfg["lam"])
            print(f"  {name} {decel:.2f} m/s^2 {rail}: f_min = {f_req:.6f}"
                  + ("  -> NIEOSIAGALNE przy kazdym ukladzie osi" if f_req > 1.0 else ""))
        mu_req = required_adhesion(decel, ALL_AXLES_BRAKED_MASS_FRACTION, cfg["lam"])
        print(f"  {name} {decel:.2f} m/s^2 przy f=1: mu_min = {mu_req:.6f}")
    print()
    print("DROGA HAMOWANIA, hamulec sluzbowy, krok 1/120 s")
    print("v0[km/h]  wzor[m]   bez_oporow[m]  tunel[m]  powierzchnia[m]  dS_tunel  dS_pow  "
          "dS_tunel_z_energii  dS_pow_z_energii")
    for row in distance_table(cfg):
        print(f"{row['start_kmh']:8.0f}  {row['closed_form_m']:8.3f}  {row['kinematic_m']:13.3f}  "
              f"{row['tunnel_m']:8.3f}  {row['surface_m']:15.3f}  {row['tunnel_shortening_m']:8.3f}  "
              f"{row['surface_shortening_m']:6.3f}  {row['tunnel_shortening_from_energy_m']:18.3f}  "
              f"{row['surface_shortening_from_energy_m']:16.3f}")
    print()
    print("SOLVER PUNKTU HAMOWANIA (bez oporow, z ograniczeniem zrywu)")
    v0 = cfg["max_speed_kmh"] / 3.6
    print(f"  minimum ze zrywu z {cfg['max_speed_kmh']:.0f} km/h do 0 = "
          f"{minimum_distance_m(v0, 0.0, cfg['jerk']):.3f} m "
          f"(b_progowe = {plateau_ceiling_mps2(v0, 0.0, cfg['jerk']):.4f} m/s^2)")
    for distance in (150.0, 200.0, 240.0, 300.0, 400.0):
        b = required_deceleration_mps2(v0, 0.0, distance, cfg["jerk"])
        back = braking_distance_m(v0, 0.0, b, cfg["jerk"])
        print(f"  s = {distance:6.1f} m -> b = {b:.6f} m/s^2, kontrola s(b) = {back:.6f} m, "
              f"|delta| = {abs(back - distance):.3e} m")


if __name__ == "__main__":
    report()
