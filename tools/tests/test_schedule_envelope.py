#!/usr/bin/env python3
"""Testy koperty prędkości: rozkład kontra model fizyki M7.

Sprawdzają **własności modelu**, a nie wybrane liczby dla Brukseli. Liczba dla
konkretnego odcinka zależy od rozkładu, który się zmienia; własność „krótszy czas
wymaga wyższej prędkości" nie zmienia się nigdy i to ona pilnuje, żeby dolne
ograniczenie było dolnym ograniczeniem.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

import braking as B  # noqa: E402
import schedule_envelope as SE  # noqa: E402

CFG = B.params()


def _model():
    return SE.Model(CFG["aw0_kg"], CFG)


def _segment(distance_m, scheduled_s, package="L1_A", from_stop="A", to_stop="B", line="1"):
    return {"package": package, "line": line, "direction_id": "0",
            "from_stop": from_stop, "to_stop": to_stop,
            "from_name": from_stop, "to_name": to_stop,
            "distance_m": distance_m, "median_s": scheduled_s}


# --- hamowanie ----------------------------------------------------------------

def test_envelope_brake_below_the_plateau_ignores_the_commanded_deceleration():
    """Przy małej prędkości cel wypada w trakcie narastania hamulca, więc zadane `b`
    nie zdąży zadziałać — dwie różne wartości `b` muszą dać tę samą drogę."""
    # Sufit plateau to sqrt(2*j*v); dla j = 0,75 hamulec służbowy 1,10 m/s² przestaje
    # być osiągalny dopiero poniżej 0,81 m/s. 1,0 m/s jeszcze PLATEAU osiąga.
    slow = 0.5
    low, _t = SE.brake_profile(slow, 1.10, CFG["jerk"])
    high, _t2 = SE.brake_profile(slow, 3.00, CFG["jerk"])
    assert abs(low - high) < 1e-12
    assert abs(low - B.ramp_only_distance_m(slow, 0.0, CFG["jerk"])) < 1e-12


def test_envelope_brake_above_the_plateau_uses_the_closed_form():
    fast = 80.0 / 3.6
    distance, time = SE.brake_profile(fast, CFG["service"], CFG["jerk"])
    assert abs(distance - B.braking_distance_m(fast, 0.0, CFG["service"], CFG["jerk"])) < 1e-12
    assert abs(time - B.braking_time_s(fast, 0.0, CFG["service"], CFG["jerk"])) < 1e-12


def test_envelope_standstill_brake_is_zero_not_a_negative_closed_form():
    assert SE.brake_profile(0.0, CFG["service"], CFG["jerk"]) == (0.0, 0.0)


# --- czas przejazdu -----------------------------------------------------------

def test_envelope_higher_ceiling_is_never_slower():
    """Monotoniczność jest warunkiem, żeby bisekcja po prędkości w ogóle miała sens."""
    model = _model()
    previous = None
    for speed in (30.0, 40.0, 50.0, 60.0, 70.0, 80.0):
        current = model.fastest_time_s(1200.0, speed)
        if previous is not None:
            assert current <= previous + 1e-9, (speed, current, previous)
        previous = current


def test_envelope_short_segment_never_reaches_the_ceiling():
    """Na krótkim odcinku profil jest trójkątem: podniesienie sufitu nic nie zmienia."""
    model = _model()
    short = 200.0
    assert abs(model.fastest_time_s(short, 60.0) - model.fastest_time_s(short, 100.0)) < 1e-6
    peak = model.peak_speed_kmh(short, 100.0)
    assert peak < 60.0
    _t_a, s_a = model.accel(peak)
    s_b, _t_b = model.brake(peak)
    assert abs(s_a + s_b - short) < 1.0


def test_envelope_long_segment_mean_speed_approaches_the_ceiling():
    model = _model()
    distance = 20000.0
    mean = 3.6 * distance / model.fastest_time_s(distance, 70.0)
    assert 60.0 < mean < 70.0


# --- dolne ograniczenie prędkości ---------------------------------------------

def test_envelope_minimum_top_speed_just_fits_the_schedule():
    """Znaleziona prędkość ma mieścić się w rozkładzie, a o włos niższa już nie."""
    model = _model()
    distance, scheduled = 900.0, 70.0
    speed = model.minimum_top_speed_kmh(distance, scheduled)
    assert speed is not None
    assert model.fastest_time_s(distance, speed) <= scheduled + 1e-6
    assert model.fastest_time_s(distance, speed - 1.0) > scheduled


def test_envelope_tighter_schedule_demands_a_higher_speed():
    model = _model()
    loose = model.minimum_top_speed_kmh(900.0, 90.0)
    tight = model.minimum_top_speed_kmh(900.0, 65.0)
    assert tight > loose


def test_envelope_impossible_schedule_returns_none_not_the_ceiling():
    """Rozkład, którego model nie dowozi, ma wyjść jako nierealizowalny. Zwrócenie
    sufitu przeszukiwania zamieniłoby błąd danych w fałszywy pomiar prędkości."""
    model = _model()
    assert model.minimum_top_speed_kmh(900.0, 5.0) is None


def test_envelope_generous_schedule_still_needs_a_positive_speed():
    model = _model()
    speed = model.minimum_top_speed_kmh(900.0, 600.0)
    assert speed is not None and speed > 0.0


# --- raport -------------------------------------------------------------------

def test_envelope_counts_a_shared_track_segment_once():
    """Pień 1/5 i pierścień 2/6 to ten sam tor obsługiwany przez dwie linie. Policzony
    dwa razy zawyżyłby liczbę odcinków i podwoił wagę pnia w statystyce."""
    timetable = {"segments": [_segment(900.0, 70.0, line="1"),
                              _segment(900.0, 70.0, line="5")]}
    report = SE.envelope(timetable, "AW0", CFG)
    assert report["segments"] == 1


def test_envelope_different_track_with_the_same_stops_on_another_package_is_separate():
    timetable = {"segments": [_segment(900.0, 70.0, package="L1_A"),
                              _segment(900.0, 70.0, package="L2_E")]}
    assert SE.envelope(timetable, "AW0", CFG)["segments"] == 2


def test_envelope_binding_segment_is_the_one_demanding_most_speed():
    timetable = {"segments": [_segment(900.0, 90.0, from_stop="wolny"),
                              _segment(900.0, 66.0, from_stop="szybki")]}
    report = SE.envelope(timetable, "AW0", CFG)
    assert report["binding_segment"]["from_name"] == "szybki"
    assert report["network_min_top_speed_kmh"] == report["binding_segment"]["min_top_speed_kmh"]
    for row in report["rows"]:
        assert row["min_top_speed_kmh"] <= report["network_min_top_speed_kmh"] + 1e-9


def test_envelope_reports_infeasible_segments_instead_of_dropping_them():
    timetable = {"segments": [_segment(900.0, 5.0, from_stop="niemozliwy"),
                              _segment(900.0, 70.0, from_stop="normalny")]}
    report = SE.envelope(timetable, "AW0", CFG)
    assert report["segments"] == 2 and report["infeasible"] == 1
    assert report["binding_segment"]["from_name"] == "normalny"


def test_envelope_ignores_segments_without_a_measured_distance():
    timetable = {"segments": [{"median_s": 70.0}, _segment(900.0, 70.0)]}
    assert SE.envelope(timetable, "AW0", CFG)["segments"] == 1


def test_envelope_loaded_train_needs_at_least_as_much_speed_as_the_empty_one():
    """AW2 rozpędza się wolniej, więc ten sam rozkład wymaga nie mniejszej prędkości."""
    timetable = {"segments": [_segment(900.0, 70.0)]}
    empty = SE.envelope(timetable, "AW0", CFG)["network_min_top_speed_kmh"]
    loaded = SE.envelope(timetable, "AW2", CFG)["network_min_top_speed_kmh"]
    assert loaded >= empty


def test_envelope_reserve_is_measured_against_the_unconstrained_run():
    timetable = {"segments": [_segment(900.0, 70.0)]}
    row = SE.envelope(timetable, "AW0", CFG)["rows"][0]
    assert abs(row["reserve_vs_unconstrained_s"]
               - (row["scheduled_s"] - row["unconstrained_time_s"])) < 0.01
    assert row["reserve_vs_unconstrained_s"] > 0.0


def test_envelope_carries_the_braking_parameters_it_actually_used():
    """Liczba bez wpisanych obok parametrów modelu jest nieodtwarzalna."""
    report = SE.envelope({"segments": [_segment(900.0, 70.0)]}, "AW0", CFG)
    assert report["service_brake_mps2"] == CFG["service"]
    assert report["jerk_mps3"] == CFG["jerk"]
    assert report["mass_kg"] == CFG["aw0_kg"]


# --- co przeżywało mutację ------------------------------------------------------

def test_envelope_any_positive_speed_still_has_a_braking_distance():
    """Próg strażnika postoju ma stać na ZERZE, nie na małej liczbie dodatniej.

    Zmierzone 03.09.2026 audytem mutacyjnym: `v0_ms <= 0.0` -> `v0_ms <= 0.001`
    przeżywało. `test_envelope_standstill_brake_is_zero_not_a_negative_closed_form`
    sprawdza wyłącznie v0 = 0, a przesunięty próg zwraca (0, 0) dla wszystkiego poniżej
    0,001 m/s — przy 0,001 m/s zamiast 3,44e-5 m i 0,0516 s wychodzi „pociąg już stoi".
    Pociąg stojący i pociąg toczący się 3,6 mm/s to dwa różne zdarzenia: drugi ma
    jeszcze drogę do przejechania i strażnik nie ma prawa mu jej odbierać.

    Granica jest tu ZEREM, więc trafia się w nią dokładnie i bez zastrzeżeń: `v0 == 0.0`
    jest równością ścisłą (zero jest jedyną wartością, przy której odejmowanie
    zmiennoprzecinkowe nie gubi nic). Wartości po dodatniej stronie bierzemy w kilku
    rzędach wielkości, żeby przesunięcie progu w JAKIEKOLWIEK miejsce dodatnie
    zostało zauważone.
    """
    assert SE.brake_profile(0.0, CFG["service"], CFG["jerk"]) == (0.0, 0.0)
    for v0 in (1e-9, 1e-6, 1e-4, 0.001, 0.01, 0.1):
        distance, time = SE.brake_profile(v0, CFG["service"], CFG["jerk"])
        assert distance > 0.0 and time > 0.0, v0
        # Przy tak małej prędkości cel wypada w trakcie narastania hamulca, więc
        # obowiązuje sam zryw — druga droga do tej samej liczby.
        assert distance == B.ramp_only_distance_m(v0, 0.0, CFG["jerk"]), v0
        assert time == (2.0 * v0 / CFG["jerk"]) ** 0.5, v0


def test_envelope_schedule_equal_to_the_floor_time_is_feasible_not_infeasible():
    """Rozkład równy CO DO BITU najkrótszemu możliwemu czasowi jest realizowalny.

    Zmierzone 03.09.2026: `fastest_time_s(...) > scheduled_s` -> `>=` w bramce
    realizowalności przeżywało. Skutek nie jest kosmetyczny: odcinek dostaje `None`,
    wpada do licznika `infeasible`, wypada z sortowania i przestaje móc być odcinkiem
    wiążącym — a to on wyznacza dolne ograniczenie prędkości dla całej sieci.

    W granicę trafiamy DOKŁADNIE, bo rozkładowy czas jest tu WYLICZONY tym samym
    wywołaniem `fastest_time_s`, którego wynik bramka potem porównuje: ten sam model,
    ten sam cache prędkości, ten sam bit. Wariant „prawie na granicy" nie zadziałałby:
    `(t + 1e-9) - t` nie jest 1e-9, więc dodanie epsilonu mija granicę zamiast w nią
    trafić. Zejście o JEDEN bit robi `math.nextafter`, i to jest kontrola negatywna
    poniżej.
    """
    model = _model()
    for distance in (200.0, 900.0, 1500.0):
        floor = model.fastest_time_s(distance, SE.SEARCH_CEILING_KMH)
        speed = model.minimum_top_speed_kmh(distance, floor)
        assert speed is not None, (
            f"{distance} m w {floor} s: rozkład równy czasowi granicznemu ma być "
            "realizowalny, a nie odrzucony jako za ciasny")
        assert model.fastest_time_s(distance, speed) <= floor, (distance, speed)
    # Kontrola: o jeden bit ciaśniejszy rozkład JEST nierealizowalny.
    floor = model.fastest_time_s(900.0, SE.SEARCH_CEILING_KMH)
    assert model.minimum_top_speed_kmh(900.0, math.nextafter(floor, 0.0)) is None


def test_envelope_minimum_speed_never_exceeds_a_speed_known_to_fit():
    """Remis w bisekcji prędkości musi iść na stronę „mieści się".

    Zmierzone 03.09.2026: `fastest_time_s(distance_m, mid) > scheduled_s` -> `>=`
    przeżywało. Na długim odcinku kosztuje to jeden krok bisekcji, czyli 1,1e-10 km/h
    i nic więcej. Na KRÓTKIM odcinku jest inaczej: powyżej prędkości szczytowej trójkąta
    czas przejazdu przestaje zależeć od sufitu, więc odrzucony remis wyrzuca całą tę
    płaską półkę naraz. Zmierzone: 200 m z rozkładem 26,00 s wychodzi wtedy jako
    90,00 km/h zamiast 52,03 km/h. To 38 km/h błędu w liczbie, która ma być DOLNYM
    ograniczeniem prędkości liniowej sieci — czyli w jedynym wyniku tego modułu.

    Test nie przypina żadnej z tych liczb, bo obie zależą od rozkładu. Przypina
    niezawodną implikację: skoro sufit `v` dowozi rozkład `T`, to najmniejszy sufit
    dowożący `T` nie może być od `v` WYŻSZY. W granicę trafiamy dokładnie, bo `T` jest
    wyliczone jako `fastest_time_s(d, v)` tym samym wywołaniem, które bisekcja powtórzy
    dla `mid == v`; przy 40 podziałach przedziału (0, 120) środki 60,0 i 30,0 są
    dokładne w dwójce, więc porównanie wypada na ścisłej równości.
    """
    model = _model()
    for distance in (200.0, 900.0, 1500.0):
        for anchor in (0.5 * SE.SEARCH_CEILING_KMH, 0.25 * SE.SEARCH_CEILING_KMH):
            scheduled = model.fastest_time_s(distance, anchor)
            speed = model.minimum_top_speed_kmh(distance, scheduled)
            assert speed is not None, (distance, anchor)
            assert speed <= anchor, (
                f"{distance} m: {anchor} km/h dowozi rozkład {scheduled} s, więc "
                f"najmniejszy sufit nie może wyjść wyżej — wyszedł {speed}")
    # Odcinek krótki, na którym ta pomyłka kosztuje najwięcej: sufit przeszukiwania
    # nie jest osiągany, bo profil jest trójkątem.
    short = 200.0
    assert model.peak_speed_kmh(short, SE.SEARCH_CEILING_KMH) < 0.5 * SE.SEARCH_CEILING_KMH


def test_envelope_bisection_guard_does_not_truncate_a_very_loose_schedule():
    """Strażnik bisekcji ma stać na ZERZE — dodatni próg ucina wyszukiwanie w pół drogi.

    Zmierzone 03.09.2026: `mid <= 0.0` -> `mid <= 0.001` przeżywało. Przy rozkładzie
    tak luźnym, że wystarcza ułamek km/h, bisekcja schodzi poniżej 0,001 km/h;
    przesunięty próg przerywa ją w tym miejscu i zwraca 0,00183 km/h zamiast
    0,0005 km/h. Zwrócona liczba przestaje być NAJMNIEJSZYM sufitem mieszczącym się
    w rozkładzie, a moduł liczy właśnie dolne ograniczenie — zawyżenie go trzy i pół
    raza jest zawyżeniem całego wyniku.

    Test nie przypina liczby, tylko WŁASNOŚĆ ciasności: zwrócona prędkość ma mieścić
    się w rozkładzie, a obniżona o promil — już nie. Rozdzielczość bisekcji na
    przedziale (0, 120) po 40 podziałach to ok. 1,1e-10 km/h, czyli o rzędy wielkości
    mniej niż ten promil; własność jest więc prawdziwa dla poprawnej implementacji
    przy każdej z badanych par, a fałszywa, gdy strażnik obetnie wyszukiwanie.
    """
    model = _model()
    for distance, scheduled in ((900.0, 90.0), (900.0, 1.0e5), (900.0, 6.48e6),
                                (200.0, 1.0e9), (1500.0, 120.0)):
        speed = model.minimum_top_speed_kmh(distance, scheduled)
        assert speed is not None and speed > 0.0, (distance, scheduled)
        assert model.fastest_time_s(distance, speed) <= scheduled, (distance, scheduled)
        assert model.fastest_time_s(distance, speed * 0.999) > scheduled, (
            f"{distance} m / {scheduled} s: {speed} km/h nie jest NAJMNIEJSZYM sufitem "
            "mieszczącym się w rozkładzie — bisekcja została ucięta")

# --- 6.D137: czy wybrana masa jest przybliżona -----------------------------------

def test_przyblizona_jest_jedna_z_dwoch_mas_a_nie_obie():
    """Sedno pozycji: rozróżnienie, a nie powtórzona linijka.

    `aw0_kg` czyta `parameters.empty_mass_kg` z flagą `approximate: true` („STIB states
    approximately 170 tonnes"), `aw2_kg` czyta `reference_model.aw2_model_mass_kg`
    o statusie `design_model` — świadome założenie symulatora, nie przybliżenie źródła.
    """
    przybliżona, notatka = SE.masa_przybliżona("AW0")
    assert przybliżona is True, (
        "AW0 przestała być przybliżona — sprawdź `approximate` przy "
        "`parameters.empty_mass_kg` w rejestrze")
    assert "approximately" in notatka, (
        "notatka o przybliżeniu AW0 nie pochodzi z rejestru: %r" % notatka)

    obciazona, nota_obciazonej = SE.masa_przybliżona("AW2")
    assert obciazona is False, (
        "AW2 zgłoszona jako przybliżona — to jest `design_model`, czyli założenie "
        "symulatora, a nie niepewność źródła")
    assert nota_obciazonej == "", nota_obciazonej


def test_flaga_przyblizenia_idzie_Z_REJESTRU_a_nie_z_nazwy_wariantu():
    """Kontrola przyrządu: rejestr probny z odwróconymi flagami odwraca odpowiedź.

    Gdyby funkcja rozpoznawała przybliżenie po napisie „AW0", zachowałaby się tak samo
    na rejestrze, w którym przybliżona jest masa obciążona — czyli mierzyłaby własną
    nazwę zamiast danych.
    """
    # Kopia PŁYTKA całego rejestru plus własne kopie dwóch sekcji — rejestr niesie
    # na najwyższym poziomie także napisy (`schema_version`, `vehicle_id`), więc
    # „kopiuj każdą wartość jako słownik" wywraca się na pierwszym z nich.
    rejestr = B.load_registry()
    probny = dict(rejestr)
    probny["parameters"] = dict(rejestr["parameters"])
    probny["reference_model"] = dict(rejestr["reference_model"])
    probny["parameters"]["empty_mass_kg"] = dict(
        probny["parameters"]["empty_mass_kg"], approximate=False, notes="")
    probny["reference_model"]["aw2_model_mass_kg"] = dict(
        probny["reference_model"]["aw2_model_mass_kg"],
        approximate=True, notes="wejście syntetyczne kontroli")

    assert SE.masa_przybliżona("AW0", probny) == (False, ""), (
        "AW0 nadal przybliżona na rejestrze, w którym flagi nie ma — odpowiedź "
        "nie pochodzi z danych")
    assert SE.masa_przybliżona("AW2", probny) == (True, "wejście syntetyczne kontroli"), (
        "AW2 nieprzybliżona na rejestrze, w którym flaga stoi")


def test_odwzorowanie_wariantu_na_parametr_ma_jedno_zrodlo_i_odrzuca_obce():
    """Nieznany wariant to BŁĄD, nie cicha masa obciążona.

    Do 6.D137 stało `cfg["aw0_kg"] if mass_key == "AW0" else cfg["aw2_kg"]`, czyli
    każda nazwa spoza „AW0" — literówka `AWO`, pusty napis — dawała po cichu AW2.
    """
    assert SE.klucz_masy("AW0") == "aw0_kg", SE.klucz_masy("AW0")
    assert SE.klucz_masy("AW2") == "aw2_kg", SE.klucz_masy("AW2")
    for obcy in ("AWO", "", "aw0", "AW1"):
        try:
            SE.klucz_masy(obcy)
        except ValueError as blad:
            assert "nieznany wariant masy" in str(blad), str(blad)
        else:
            raise AssertionError(
                "wariant %r przeszedł bez błędu — cicha podmiana masy wróciła" % obcy)

    # Zbiór wariantów CLI i zbiór parametrów to ma być JEDNA lista, nie dwie:
    # dopisanie wariantu w argparse bez wpisu tutaj dawałoby `ValueError` dopiero
    # w przebiegu, a nie w bramce.
    zrodlo = open(os.path.join(ROOT, "tools", "physics", "schedule_envelope.py"),
                  encoding="utf-8").read()
    assert 'choices=sorted(PARAMETR_MASY)' in zrodlo or \
           'choices=("AW0", "AW2")' in zrodlo, (
        "argparse trzyma własną listę wariantów masy — ma czytać `PARAMETR_MASY`")


def test_raport_niesie_flage_przyblizenia_obok_masy():
    """Plik ma mówić to samo, co konsola — inaczej zdanie ginie przy czytaniu JSON-a."""
    timetable = {"segments": [_segment(600.0, 60.0)]}
    pusty = SE.envelope(timetable, "AW0", CFG)
    obciazony = SE.envelope(timetable, "AW2", CFG)

    assert pusty["mass_approximate"] is True, (
        "raport AW0 nie niesie flagi przybliżenia (%r) — zdanie z konsoli ginie "
        "przy czytaniu pliku" % pusty["mass_approximate"])
    assert "approximately" in pusty["mass_approximate_note"], (
        "notatka w raporcie AW0 nie pochodzi z rejestru: %r"
        % pusty["mass_approximate_note"])
    assert obciazony["mass_approximate"] is False, (
        "raport AW2 zgłasza przybliżenie (%r) — `design_model` przybliżeniem nie jest"
        % obciazony["mass_approximate"])
    assert obciazony["mass_approximate_note"] == "", (
        "raport AW2 niesie notatkę o przybliżeniu: %r"
        % obciazony["mass_approximate_note"])


def test_oba_warianty_maja_WYKONANY_przebieg_i_wypisy_roznia_sie_tym_zdaniem():
    """Pole „Skończone, gdy": OBA warianty przebiegnięte, różnica widoczna w wypisie.

    Przebieg idzie przez `main()` na rozkładzie syntetycznym, a nie przez samo
    `envelope` — bo to wypis jest przedmiotem pozycji, a wypis stoi w `main`.
    Rozkład syntetyczny, bo prawdziwy wymaga pobrania GTFS, którego w drzewie nie ma.
    """
    import contextlib
    import io as _io
    import json as _json
    import tempfile

    timetable = {"segments": [
        dict(_segment(485.29, 52.0), from_name="Parc", to_name="Arts-Loi"),
        dict(_segment(700.0, 62.0), from_stop="B", to_stop="C",
             from_name="Maelbeek", to_name="Schuman"),
    ]}

    wypisy = {}
    with tempfile.TemporaryDirectory(prefix="metro-koperta-") as katalog:
        sciezka = os.path.join(katalog, "timetable.json")
        with open(sciezka, "w", encoding="utf-8") as uchwyt:
            _json.dump(timetable, uchwyt)
        for wariant in ("AW0", "AW2"):
            bufor = _io.StringIO()
            with contextlib.redirect_stdout(bufor):
                kod = SE.main(["--timetable", sciezka, "--mass", wariant,
                               "--out", os.path.join(katalog, "kop-%s.json" % wariant)])
            assert kod == 0, ("przebieg %s skonczyl kodem %s" % (wariant, kod))
            wypisy[wariant] = bufor.getvalue()

    assert "masa AW0 jest PRZYBLIŻONA" in wypisy["AW0"], wypisy["AW0"][:400]
    assert "nie jest oznaczona jako przybliżona" in wypisy["AW2"], wypisy["AW2"][:400]
    assert "jest PRZYBLIŻONA" not in wypisy["AW2"], (
        "przebieg AW2 mówi o przybliżeniu — a `design_model` przybliżeniem nie jest")

    # I strona druga: zdanie o przybliżeniu stoi w OBU przebiegach, bo milczenie
    # byłoby nieodróżnialne od braku sprawdzenia (ta sama zasada, co w 6.D113
    # i 6.D132). Liczone po słowie „przybliżon", bo nagłówek też mówi „masa AW0" —
    # tam jednak o wartości, a nie o jej niepewności.
    for wariant, tekst in wypisy.items():
        zdania = [w for w in tekst.splitlines() if "przybliżon" in w.lower()]
        assert len(zdania) == 1, (
            "wariant %s ma %d zdań o przybliżeniu zamiast jednego:\n%s"
            % (wariant, len(zdania), tekst[:400]))
        assert wariant in zdania[0], (
            "zdanie o przybliżeniu nie nazywa wariantu, którego dotyczy: %r" % zdania[0])


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
