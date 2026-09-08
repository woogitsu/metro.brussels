#!/usr/bin/env python3
"""Bramka kosztu kroku `LineCore.Step` sprawdza to, co obiecuje — i nie da sie oszukac.

**Dlaczego ten modul istnieje osobno od samej bramki.** `tools/ci/assert_linecore_budget.py`
chodzi w CI i potrzebuje `dotnet`, zeby cokolwiek zmierzyc. Zestaw narzedzi chodzi tam,
gdzie `doctor.sh` przepuszcza brak SDK, wiec testy nie moga uruchamiac `budget`. Rozbior
wyjscia, prog i warunki werdyktu da sie jednak sprawdzic bez ani jednego przejazdu —
i to jest cala zawartosc tego pliku.

**Czego pilnuje najmocniej.** Nie liczby mikrosekund, tylko tego, ze pomiar dotyczy
DZIEWIECIU skladow. 6.A12 (#308) zmierzyla, ze `budget --trains 32` melduje `N_max = 1`,
kiedy okno jest krotsze niz jeden odstep — kolumna µs/krok ma wtedy wartosc, tylko
opisuje inny przejazd. Bramka czytajaca sama liczbe mikrosekund przechodzilaby na
zielono z pomiarem jednego skladu.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "ci"))

import assert_linecore_budget as gate  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "sim-tests.yml")
BRAMKA = os.path.join(ROOT, "tools", "ci", "assert_linecore_budget.py")

#: Zdanie prozy twierdzące, ILE wynosi próg — czyli kopia wartości w innym miejscu
#: niż konfiguracja. 6.D56: taka kopia stała w docstringu `assert_linecore_budget.py`
#: („próg 8,0 µs") przy progu 14,0 w konfiguracji, i nie widziała jej żadna bramka.
#:
#: `ó` STOI TU JAWNIE i to nie jest ozdoba: pierwsza wersja tego wzorca zaczynała się
#: od `\bpro`, więc NIE pasowała do słowa „próg" i dawała zero trafień na pliku,
#: w którym usterka stała. Wzorzec bez tej litery byłby bramką zieloną nad usterką.
KOPIA_PROGU_W_PROZIE = re.compile(r"\bpr[oó]g\w*\b[^\n]{0,40}?\d+[.,]\d+",
                                 re.IGNORECASE)

#: Od jakiego wcięcia wiersz docstringa jest WKLEJONYM WYJŚCIEM, a nie prozą.
#: Rozróżnienie jest konieczne, bo `niemierzalny()` cytuje datowany wypis przebiegu
#: z 07.09.2026, w którym stoi próg obowiązujący WTEDY — i przepisanie tej liczby
#: pod dzisiejszą wartość zamieniłoby zapis pomiaru na zapis zmyślony (`CLAUDE.md`
#: §5). To ten sam trójpodział, który 6.D49 zmierzyło na nazwach testów: żywy
#: odsyłacz, wklejone wyjście pomiaru i zdanie o historii — wolno tknąć tylko
#: pierwszy. Zmierzone 08.09.2026: proza tego pliku ma wcięcie 0 lub 4, wklejone
#: wypisy mają 8.
WCIECIE_WKLEJONEGO_WYJSCIA = 8

#: Wiersz pomiaru w ksztalcie, jaki daje `Sim.Runner budget` — dziewiec skladow
#: na planie, koszt kroku z zapasem do progu.
ZIELONY = (
    "[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu\n"
    "[BUDŻET] 32;9;5.08;0.98;265081;223360;268544;17.0;3.772;1.01;0.05\n"
)

#: Ten sam wiersz, ale z kosztem kroku PONAD progiem — atrapa odmowy czasowej.
#: Byla wpisana w TRZECH miejscach jako `.replace(...)` z wartoscia 9.091, i to
#: przestalo dzialac 08.09.2026, kiedy prog poszedl z 8,0 na 14,0: 9,091 us miesci sie
#: dzis w progu, wiec trzy testy zadajace odmowy zadalyby jej od pomiaru ZIELONEGO.
#: Wartosc stoi teraz w JEDNYM miejscu, a `test_atrapa_WOLNA_lezy_POWYZEJ_progu`
#: pilnuje, zeby przy nastepnym ruchu progu nie zostala w tyle po cichu.
WOLNY = ZIELONY.replace(";3.772;1.01;0.05", ";15.500;1.00;0.19")


def _config():
    return gate.load_config()


def _gate_step(workflow):
    """Blok `run:` kroku, ktory wola bramke — bez kroku kontroli negatywnej."""
    at = workflow.index("- name: Core step cost at nine trains is under budget")
    end = workflow.index("- name: Core step gate can actually go red", at)
    return workflow[at:end]


def _kontrola_step(workflow):
    """Blok `run:` kroku kontroli negatywnej bramki kosztu kroku."""
    at = workflow.index("- name: Core step gate can actually go red")
    end = workflow.index("- name: Braking reference matches the core byte for byte", at)
    return workflow[at:end]


def test_the_threshold_lives_in_one_place_and_the_step_does_not_compare_anything():
    """Prog w YAML-u i prog w pliku to dwie liczby, ktore rozjada sie przy pierwszej
    zmianie. Krok CI ma WOLAC skrypt, a nie porownywac samodzielnie.

    Sprawdzany jest sam krok bramki, nie caly plik: krok kontroli negatywnej NIZEJ
    zawiera zmyslone liczby pomiaru i to jest w porzadku — one wlasnie maja byc
    literalami, bo udaja wyjscie `budget`.

    **Uzasadnienie wyzej bylo prawdziwe dla WSZYSTKICH kolumn dokladnie do 08.09.2026
    i zlamalo sie na jednej.** Kolumny opisujace KSZTALT przejazdu (obsada, mediany,
    rozstep) sa od progu niezalezne i literalami zostaja. Kolumna µs/krok atrapy
    „wolnej" musi lezec POWYZEJ progu, zeby kontrola negatywna cokolwiek znaczyla —
    a literal 9.091 przy progu podniesionym na 14,0 znalazl sie PONIZEJ i kontrola
    zaczerwienila sie zdaniem „bramka przyjela krok wolniejszy od progu" o pomiarze,
    ktory wolniejszy nie byl (job 101988401447, krok 17, 08.09.2026). Ta jedna kolumna
    jest dzis WYLICZANA z progu, a pilnuje tego
    `test_atrapa_w_KROKU_CI_nie_jest_literalem_ponizej_progu`.
    """
    config = _config()
    with open(WORKFLOW, encoding="utf-8") as handle:
        workflow = handle.read()
    assert "tools/ci/assert_linecore_budget.py" in workflow, (
        "workflow nie wola bramki kosztu kroku")
    krok = _gate_step(workflow)
    assert "tools/ci/assert_linecore_budget.py" in krok, krok
    for liczba in (repr(config["microseconds_per_step_max"]),
                   str(config["scenario"]["steps"]),
                   str(config["scenario"]["headway_s"])):
        assert liczba not in krok, (
            "liczba %s stoi wpisana w kroku CI — ma byc TYLKO w "
            "tools/ci/linecore-step-budget.json" % liczba)
    for porownanie in ("bc ", "awk ", "-gt ", "-lt ", "expr "):
        assert porownanie not in krok, (
            "krok porownuje cos sam (%r) zamiast zdac sie na skrypt" % porownanie)

    # ROZSZERZENIE 6.D56: „jedno miejsce" znaczy jedno w CAŁYM drzewie, nie jedno
    # w YAML-u. Do 08.09.2026 ta asercja czytała WYŁĄCZNIE krok CI, więc commit
    # #408 — którego tematem było „liczba ma stać w jednym miejscu" — przepisał
    # zdanie o progu w JSON-ie i zostawił kopię w docstringu samej bramki
    # (`assert_linecore_budget.py`), gdzie stała wartość już nieprawdziwa. Bramka
    # jednego miejsca przegapiła drugie miejsce, bo nie patrzyła.
    #
    # Sprawdzane jest DWOJE, w treści `.py` bramki:
    #   1. że nie stoi tam liczba `steps` ze scenariusza (120000) — wartość długa,
    #      więc szukanie podciągu nie daje fałszywych trafień (zmierzone: 0);
    #   2. że żadne zdanie PROZY nie twierdzi, ile wynosi próg.
    #
    # DLACZEGO NIE SPRAWDZAMY TAK `headway_s` I `trains_on_line_expected`, i to
    # jest wynik pomiaru, nie przeoczenie: ich wartości to 90 i 9, a szukanie
    # podciągu daje w tym pliku odpowiednio 1 i 17 trafień — same daty
    # (`05.09.2026`), indeksy grup (`group(9)`) i liczby z ekstrapolacji
    # (`330–390`). Bramka z takim wskaźnikiem fałszywych alarmów idzie do
    # wyłączenia (6.D27), więc te dwie liczby zostają pilnowane TAM, gdzie
    # otaczający tekst jest krótki: w kroku CI, wyżej w tej samej funkcji.
    with open(BRAMKA, encoding="utf-8") as handle:
        zrodlo_bramki = handle.read().split("\n")

    dlugie = str(config["scenario"]["steps"])
    stoi = [n for n, w in enumerate(zrodlo_bramki, 1) if dlugie in w]
    assert not stoi, (
        "liczba %s ze scenariusza stoi w tresci bramki, w wierszach %s — ma byc "
        "TYLKO w tools/ci/linecore-step-budget.json" % (dlugie, stoi))

    kopie = [(n, w.strip()) for n, w in enumerate(zrodlo_bramki, 1)
             if KOPIA_PROGU_W_PROZIE.search(w)
             and (len(w) - len(w.lstrip())) < WCIECIE_WKLEJONEGO_WYJSCIA]
    assert not kopie, (
        "proza bramki twierdzi, ile wynosi prog — to kopia wartosci poza "
        "konfiguracja i rozjedzie sie przy pierwszej zmianie progu:\n"
        + "\n".join("  %s: %s" % (n, w[:100]) for n, w in kopie))


def test_datowany_zapis_pomiaru_NIE_jest_kopia_progu_i_bramka_o_nim_milczy():
    """Druga strona pary do rozszerzenia z 6.D56 — bez niej tamta asercja idzie do
    wyłączenia przy pierwszym fałszywym alarmie (6.D27).

    `niemierzalny()` cytuje w docstringu **datowany wypis przebiegu** z 07.09.2026,
    w którym stoi próg obowiązujący WTEDY. Ta liczba jest **prawdą o tamtym dniu**
    i przepisanie jej pod dzisiejszą wartość zamieniłoby zapis pomiaru na zapis
    zmyślony — czego zabrania `CLAUDE.md` §5, i to w pliku, którego cała wartość
    polega na tym, że wypisy są prawdziwe. To ten sam trójpodział, który 6.D49
    zmierzyło na nazwach testów: **żywy odsyłacz**, **wklejone wyjście pomiaru**
    i **zdanie o historii** — wolno tknąć tylko pierwszy.

    Ten test przybija rozróżnienie z dwóch stron naraz, więc nie da się go spełnić
    przez poszerzenie progu wcięcia: żąda, żeby w tym pliku **istniał** wklejony
    wypis z wartością progu (inaczej rozróżnienie byłoby martwe i nikt by nie
    zauważył, że zniknęło) i żeby jednocześnie **żadna proza** takiej wartości nie
    nosiła.
    """
    with open(BRAMKA, encoding="utf-8") as handle:
        wiersze = handle.read().split("\n")
    wklejone = [n for n, w in enumerate(wiersze, 1)
                if KOPIA_PROGU_W_PROZIE.search(w)
                and (len(w) - len(w.lstrip())) >= WCIECIE_WKLEJONEGO_WYJSCIA]
    proza = [n for n, w in enumerate(wiersze, 1)
             if KOPIA_PROGU_W_PROZIE.search(w)
             and (len(w) - len(w.lstrip())) < WCIECIE_WKLEJONEGO_WYJSCIA]
    assert wklejone, (
        "w tresci bramki nie ma ani jednego WKLEJONEGO wypisu z wartoscia progu — "
        "rozroznienie proza/zapis-pomiaru przestalo cokolwiek znaczyc, wiec "
        "rozszerzenie z 6.D56 nie jest juz sprawdzane przeciwko niczemu")
    assert not proza, (
        "proza bramki nosi wartosc progu w wierszach %s" % proza)


def test_a_green_measurement_passes():
    ok, problems = gate.verdict(_config(), ZIELONY)
    assert ok, problems


def test_a_slow_step_is_refused():
    wolny = WOLNY
    ok, problems = gate.verdict(_config(), wolny)
    assert not ok
    assert any("prog" in p for p in problems), problems


def test_one_train_reported_as_nine_is_refused():
    """Sedno bramki. Pomiar jednego skladu ma TE SAMA kolumne µs/krok i miesci sie
    w progu z ogromnym zapasem — odrzucenie musi wynikac z obsady, nie z czasu."""
    jeden = ZIELONY.replace("32;9;5.08;0.98;", "32;1;1.00;0.00;")
    ok, problems = gate.verdict(_config(), jeden)
    assert not ok
    assert any("skladow" in p or "składów" in p for p in problems), problems
    assert not any("prog" in p and "us" in p for p in problems), (
        "odrzucenie ma wynikac z obsady, a nie z przekroczonego czasu: %s" % problems)


def test_an_empty_output_is_refused_instead_of_passing_quietly():
    ok, problems = gate.verdict(_config(), "nic tu nie ma\n")
    assert not ok
    assert problems


def test_more_than_one_measurement_row_is_refused():
    """Prog dotyczy jednej obsady. Dwa wiersze znacza, ze ktos zmienil scenariusz
    na drabinke N i bramka porownywalaby prog ze srednia z czegos innego."""
    dwa = ZIELONY + "[BUDŻET] 8;8;5.12;0.36;242813;224687;248859;10.0;4.118;0.99;0.05\n"
    ok, problems = gate.verdict(_config(), dwa)
    assert not ok
    assert any("JEDEN" in p for p in problems), problems


def test_the_command_is_built_from_the_config_not_from_memory():
    config = _config()
    argv = gate.command(config)
    for name, key in (("--headway-s", "headway_s"), ("--steps", "steps"),
                      ("--trains", "trains_declared"), ("--turnback-s", "turnback_s")):
        assert name in argv, name
        assert argv[argv.index(name) + 1] == str(config["scenario"][key]), name


def test_the_config_names_its_basis_and_the_expected_occupancy():
    config = _config()
    assert config["trains_on_line_expected"] == 9, (
        "prog opisuje dziewiec skladow — inna liczba wymaga nowego pomiaru, "
        "nie podmiany stalej")
    assert config["basis"].startswith("reports/"), config["basis"]
    assert os.path.isfile(os.path.join(ROOT, config["basis"])), (
        "plik progu odsyla do raportu, ktorego nie ma: " + config["basis"])


def test_the_gate_says_which_run_it_measures():
    """Bramka ma mowic, ktory wariant przejazdu mierzy, a nie milczaco mierzyc jeden.

    **Test przepisany, nie dopisany obok.** Do 6.A18 sprawdzal, ze w zrodle bramki stoi
    tekst "--coast-from-m" i "6.A18" — czyli ze zdanie ZOSTALO NAPISANE. Zdanie napisane
    raz i wpisane na sztywno starzeje sie po cichu; ta wersja sprawdza, ze zdanie zgadza
    sie z tym, co bramka NAPRAWDE uruchamia, bo obie strony czytaja `coast_from_m`.
    """
    config = _config()
    assert "coast_from_m" in config["scenario"], (
        "scenariusz nie wypowiada sie o wybiegu, wiec zdanie o nim nie ma z czego wynikac")
    zdanie = gate.coasting(config)
    if config["scenario"]["coast_from_m"] is None:
        assert "BEZ wybiegu" in zdanie, zdanie
    else:
        assert "Z WYBIEGIEM" in zdanie, zdanie
        assert str(config["scenario"]["coast_from_m"]) in zdanie, zdanie


def test_the_sentence_about_coasting_follows_the_scenario_both_ways():
    """Oba kierunki na kopii scenariusza — bo tego wlasnie nie sprawdzal test na tekst.

    Wpisanie liczby do scenariusza ma zmienic ZDANIE i WYWOLANIE naraz; brak wybiegu ma
    usunac opcje z wywolania. Rozjazd ktoregokolwiek z tych dwoch znaczy, ze bramka mowi
    o innym przejezdzie, niz mierzy.
    """
    config = _config()
    bez = json.loads(json.dumps(config))
    bez["scenario"]["coast_from_m"] = None
    assert "BEZ wybiegu" in gate.coasting(bez)
    assert "--coast-from-m" not in gate.command(bez)

    z_wybiegiem = json.loads(json.dumps(config))
    z_wybiegiem["scenario"]["coast_from_m"] = 250
    zdanie = gate.coasting(z_wybiegiem)
    assert "Z WYBIEGIEM" in zdanie and "250" in zdanie, zdanie
    argv = gate.command(z_wybiegiem)
    assert "--coast-from-m" in argv, argv
    assert argv[argv.index("--coast-from-m") + 1] == "250", argv


def test_the_measured_scenario_still_runs_without_coasting():
    """Prog 8,0 us zmierzono 06.09.2026 na przejezdzie BEZ wybiegu, a wybieg zmienia
    przejazd, nie tylko jego koszt (N_sr 6.69 bez, 6.40 przy 120 m — zmierzone przy
    6.A18). Wlaczenie wybiegu w scenariuszu bez nowego pomiaru porownywaloby wynik
    z progiem wzietym z innego przejazdu, wiec `null` jest tu warunkiem waznosci progu,
    a nie zaniedbaniem."""
    assert _config()["scenario"]["coast_from_m"] is None, (
        "scenariusz wlaczyl wybieg — prog w tym samym pliku musi wtedy pochodzic "
        "z pomiaru Z WYBIEGIEM, razem z nowym raportem")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))


# --- 6.D41: pomiar niestabilny nie jest porownywany z progiem -----------------------

#: Ten sam wiersz co ZIELONY, ale z rozstepem powtorzen 115,9 % — dokladnie tym, ktory
#: przyszedl 07.09.2026 z runnera `woogitsu-host-08` przy dwunastu jobach naraz.
#: Kolumna µs/krok NIESIE WARTOSC W PROGU, i to jest sedno: gdyby bramka porownywala
#: tylko czas, ten pomiar przeszedlby na zielono, a nie mowi on nic o kodzie.
NIESTABILNY_W_PROGU = ZIELONY.replace(";17.0;3.772;", ";115.9;3.772;")

#: Ten sam rozstep, ale z czasem PONAD progiem — tak wygladal prawdziwy przebieg,
#: ktory bramka nazwala regresem wydajnosci.
NIESTABILNY_PONAD_PROGIEM = ZIELONY.replace(";17.0;3.772;1.01;0.05", ";115.9;16.022;1.00;0.19")


def _do_pliku(tresc, katalog):
    sciezka = os.path.join(katalog, "budget.txt")
    with open(sciezka, "w", encoding="utf-8") as handle:
        handle.write(tresc)
    return sciezka


def test_niestabilny_pomiar_NIE_JEST_porownywany_z_progiem():
    """Sedno 6.D41. Zarzutem ma byc niemierzalnosc, a NIE przekroczony prog.

    Do 07.09.2026 kolumna `rozstep_%` byla parsowana i wypisywana, ale nie asertowana:
    bramka znala liczbe mowiaca, ze jej wlasny pomiar jest niestabilny, i porownywala go
    z progiem mimo to. Zmierzone: 16,022 µs przy rozstepie 115,9 % na runnerze wobec
    4,213-4,364 µs przy rozstepie 1,9-3,7 % na tej samej tresci kodu.
    """
    ok, problems = gate.verdict(_config(), NIESTABILNY_PONAD_PROGIEM)
    assert not ok, "niestabilny pomiar przeszedl na zielono"
    assert any("rozstep" in p for p in problems), problems
    assert not any("przekracza prog" in p for p in problems), (
        "bramka nadal porownuje niestabilny pomiar z progiem: %s" % problems)


def test_niestabilny_pomiar_MIESZCZACY_SIE_w_progu_tez_jest_odmowa():
    """Gdyby bramka pytala tylko o czas, ten pomiar przeszedlby na zielono.

    Asercja jest tu na BRAK zieleni przy wartosci W PROGU — czyli na to, ze bramka
    odrzuca z powodu niemierzalnosci, a nie z powodu liczby mikrosekund.
    """
    ok, problems = gate.verdict(_config(), NIESTABILNY_W_PROGU)
    assert not ok, "pomiar z rozstepem 115,9 %% przeszedl, bo czas byl w progu"
    assert any("rozstep" in p for p in problems), problems


def test_dwa_werdykty_maja_DWA_ROZNE_kody_wyjscia():
    """Bez tego rozroznienia „nie umiem zmierzyc" jest dla wolajacego nieodroznialne
    od „rdzen zwolnil" — a pierwsze kaze powtorzyc pomiar, drugie szukac regresu."""
    import tempfile
    with tempfile.TemporaryDirectory() as katalog:
        wolny = WOLNY
        kod_wolny = gate.main(["--from-output", _do_pliku(wolny, katalog)])
        kod_niestabilny = gate.main(
            ["--from-output", _do_pliku(NIESTABILNY_PONAD_PROGIEM, katalog)])
        kod_zielony = gate.main(["--from-output", _do_pliku(ZIELONY, katalog)])

    assert kod_zielony == 0, kod_zielony
    assert kod_wolny == gate.KOD_PRZEKROCZONY, kod_wolny
    assert kod_niestabilny == gate.KOD_NIEMIERZALNY, kod_niestabilny
    assert kod_wolny != kod_niestabilny, (
        "oba werdykty wychodza tym samym kodem, wiec rozroznienia nie ma")


def test_niemierzalnosc_NIE_PRZESLANIA_zarzutu_o_obsadzie():
    """Liczba skladow na planie nie zalezy od obciazenia maszyny, wiec ten zarzut musi
    przezyc niestabilny pomiar — i wyjsc kodem 1, nie kodem niemierzalnosci."""
    import tempfile
    zly = NIESTABILNY_PONAD_PROGIEM.replace("32;9;5.08;0.98;", "32;1;1.00;0.00;")
    ok, problems = gate.verdict(_config(), zly)
    assert not ok
    assert any("skladow" in p or "składów" in p for p in problems), problems
    with tempfile.TemporaryDirectory() as katalog:
        kod = gate.main(["--from-output", _do_pliku(zly, katalog)])
    assert kod == gate.KOD_PRZEKROCZONY, (
        "pomiar niestabilny Z BLEDNA OBSADA wyszedl kodem niemierzalnosci (%d) — "
        "zarzut niezalezny od maszyny zostal przeslonięty" % kod)


def test_wolny_krok_przy_ZNOSNYM_rozstepie_nadal_jest_odmowa():
    """Kontrola, ze straznik rozstepu nie polknal prawdziwej odmowy o czasie."""
    wolny = WOLNY
    ok, problems = gate.verdict(_config(), wolny)
    assert not ok
    assert any("przekracza prog" in p for p in problems), problems


def test_granica_rozstepu_jest_POWYZEJ_udokumentowanych_pomiarow_zielonych():
    """Wlasnosc WYPROWADZONA z podstawy progu, nie liczba wpisana z reki.

    `reports/linecore-step-budget-gate.md` podaje przy kalibracji progu 8,0 µs
    „rozstęp powtórzeń w moich przebiegach do 22,5 %", a atrapa ZIELONY w tym module
    niesie 17,0 %. Granica ponizej ktorejkolwiek z tych liczb odrzucalaby pomiary,
    ktore historycznie byly zielone — czyli zamienialaby bramke na generator falszywych
    alarmow (6.D27: bramka zapalajaca sie na tekscie poprawnym zostaje wylaczona).
    """
    granica = _config()["spread_pct_max"]
    z_atrapy = float(ZIELONY.strip().splitlines()[-1].split(";")[7])
    assert z_atrapy == 17.0, z_atrapy
    assert granica > z_atrapy, (
        "granica %.1f %% odrzucalaby wlasna atrape zielona (%.1f %%)" % (granica, z_atrapy))
    assert granica > 22.5, (
        "granica %.1f %% odrzucalaby pomiary z kalibracji progu (do 22,5 %%), a te byly "
        "zielone — patrz reports/linecore-step-budget-gate.md" % granica)
    assert granica < 115.9, (
        "granica %.1f %% przepuszczalaby zaobserwowany pomiar niemierzalny (115,9 %%), "
        "czyli nie robilaby nic" % granica)


#: Najwyzszy koszt kroku, ktory bramka SAMA uznala za mierzalny (rozstep 33,9 % przy
#: granicy 50 %) i odrzucila jako przekroczenie progu 8,0 us. Zmierzone 08.09.2026 na
#: `woogitsu-linux-04`, run 34194126232 proba 1. To jest dolne ograniczenie progu.
ODRZUCONY_MIERZALNY_US = 9.572

#: Rozstep, przy ktorym powyzszy pomiar padl. Wiaze oba progi: dopoki granica rozstepu
#: go przepuszcza, tamten koszt JEST porownywany z progiem czasu.
ODRZUCONY_MIERZALNY_ROZSTEP = 33.9

#: Koszt zaobserwowany 07.09.2026 na `woogitsu-host-08` przy rozstepie 115,9 %, ktory
#: bramka nazywa NIEMIERZALNYM. To jest gorne ograniczenie progu.
NIEMIERZALNY_US = 16.022


def test_prog_kosztu_kroku_lezy_MIEDZY_pomiarem_odrzuconym_a_niemierzalnym():
    """Wlasnosc WYPROWADZONA z pomiarow, nie liczba wpisana z reki — i do 08.09.2026
    NIE BYLO JEJ WCALE: `spread_pct_max` mial swoja asercje wyprowadzona od 6.D41,
    a `microseconds_per_step_max` nie mial zadnej. Prog dalo sie ustawic na dowolna
    wartosc i zaden test by nie drgnal.

    Decyzja wlasciciela z 08.09.2026 podniosla prog PONAD najwolniejsza maszyne,
    przeciwko mojej rekomendacji. Podniesienie progu oslabia bramke, wiec w tym samym
    commicie bramka dostaje warunek, ktorego nie miala: prog musi lezec MIEDZY dwoma
    pomiarami, i oba sa zmierzone.

    Od dolu — powyzej 9,572 us, bo to najwyzszy koszt, ktory bramka porownala z progiem
    i odrzucila. Prog ponizej tej liczby wraca do stanu, ktory decyzja wlasciciela
    znosi: joby czerwienieja od obciazenia puli, nie od kodu.

    Od gory — ponizej 16,022 us, kosztu, ktory bramka nazywa niemierzalnym. Prog
    stojacy NAD liczba, ktora bramka juz widziala, przestaje byc zapasem nad
    czymkolwiek; to wlasnie ta granica nie pozwolila zastosowac metody z 06.09.2026
    (1,71x nad najwyzszym pomiarem daje 16,4 us, czyli za wysoko).
    """
    prog = _config()["microseconds_per_step_max"]
    assert prog > ODRZUCONY_MIERZALNY_US, (
        "prog %.3f us nie lezy nad pomiarem %.3f us, ktory bramka odrzucila jako "
        "MIERZALNE przekroczenie — decyzja wlasciciela z 08.09.2026 zada progu ponad "
        "najwolniejsza maszyna" % (prog, ODRZUCONY_MIERZALNY_US))
    assert prog < NIEMIERZALNY_US, (
        "prog %.3f us stoi nad kosztem %.3f us, ktory bramka nazywa niemierzalnym — "
        "zapas przestaje byc zapasem nad czymkolwiek" % (prog, NIEMIERZALNY_US))


def test_atrapa_WOLNA_lezy_POWYZEJ_progu_wiec_odmowa_nie_jest_pusta():
    """Trzy testy zadaja od atrapy WOLNY odmowy czasowej. Atrapa ponizej progu
    zamienia je w testy zadajace odmowy od pomiaru ZIELONEGO — czyli w trzy testy,
    ktore pekaja z powodu nie tego, o ktory pytaja.

    Do 08.09.2026 atrapa niosla 9,091 us przy progu 8,0 i wyrazenie bylo wpisane
    w trzech miejscach osobno. Po podniesieniu progu na 14,0 zadna z tych trzech kopii
    nie bylaby juz nad progiem, a znalezc trzeba by wszystkie trzy. Stad ta asercja:
    atrapa ma jednego pisarza i jest z progiem SPRZEZONA, nie tylko akurat wyzsza.
    """
    prog = _config()["microseconds_per_step_max"]
    kolumna = float(WOLNY.strip().splitlines()[-1].split(";")[8])
    assert kolumna > prog, (
        "atrapa odmowy czasowej niesie %.3f us przy progu %.3f us, czyli MIESCI SIE "
        "w progu — trzy testy zadajace odmowy pytaja o co innego, niz mysla"
        % (kolumna, prog))


def test_prog_i_granica_rozstepu_sa_SPRZEZONE():
    """Dolne ograniczenie progu obowiazuje TYLKO dopoki granica rozstepu przepuszcza
    pomiar, z ktorego je wzieto.

    9,572 us padlo przy rozstepie 33,9 %. Gdyby granice zaciesnic ponizej tej liczby,
    tamten przebieg przestalby byc pomiarem porownywanym z progiem i stalby sie
    niemierzalnoscia (kod 3) — a wtedy dolne ograniczenie progu jest wziete z pomiaru,
    ktorego bramka juz nie porownuje, czyli z niczego.

    Ta asercja nie zakazuje zaciesniania granicy; zada, zeby zaciesnienie ponizej
    33,9 % kazalo PRZY TEJ SAMEJ ZMIANIE wrocic do podstawy progu. Bez niej dwie stale
    rozjechalyby sie po cichu.

    **Ostatnie zdanie tego docstringa jest PRZEPISANE 08.09.2026, nie dopisane obok.**
    Mowilo: „a `$comment_spread_pct_max` wprost zapowiada, ze granica ma byc
    zaciesniana" — i przestalo byc prawda tego samego dnia. Decyzja wlasciciela
    odwrocila kierunek tej reguly: granica poszla z 50 % na 100 %, wiec komentarz
    stalej nie zapowiada juz zaciskania. Asercja zostaje bez zmiany, bo jej powod
    jest od kierunku NIEZALEZNY: podstawa progu wisi na tym, ze rozstep 33,9 %
    jest mierzalny, i zaciesnienie ponizej tej liczby — z ktorejkolwiek strony
    ktos do niej wroci — nadal odbiera progowi grunt.
    """
    config = _config()
    assert config["spread_pct_max"] > ODRZUCONY_MIERZALNY_ROZSTEP, (
        "granica rozstepu %.1f %% nie przepuszcza juz pomiaru przy %.1f %%, z ktorego "
        "wziete jest dolne ograniczenie progu (%.3f us) — przelicz podstawe progu "
        "w tej samej zmianie"
        % (config["spread_pct_max"], ODRZUCONY_MIERZALNY_ROZSTEP,
           ODRZUCONY_MIERZALNY_US))


def test_atrapa_w_KROKU_CI_nie_jest_literalem_ponizej_progu():
    """Atrapa „wolna" stala w CZTERECH kopiach, nie w trzech — i czwarta byla w YAML-u.

    Trzy kopie w tym module zlapala asercja atrapy, bo czyta stala `WOLNY`. Czwarta
    stala wpisana w kroku `Core step gate can actually go red` w
    `.github/workflows/sim-tests.yml` i zadna bramka jej nie widziala: po podniesieniu
    progu na 14,0 µs literal 9.091 znalazl sie PONIZEJ progu, bramka slusznie go
    przyjela, a kontrola negatywna wywrocila job z komunikatem o pomiarze, ktory
    wolniejszy nie byl (job 101988401447, krok 17).

    Ten test czyta wiersze `[BUDŻET]` z tresci kroku i zada, zeby kolumna µs/krok
    **nie byla literalem liczbowym ponizej progu**. Podstawienie z powloki (`%s`,
    `$zmienna`) przechodzi — o to wlasnie chodzi, zeby wartosc byla WYLICZANA. Literal
    powyzej progu tez przechodzi, bo nie klamie; test nie zakazuje literalow, zakazuje
    literalow, ktore cicho przestaja byc odmowa.
    """
    prog = _config()["microseconds_per_step_max"]
    with open(WORKFLOW, encoding="utf-8") as handle:
        krok = _kontrola_step(handle.read())

    wiersze = [w for w in krok.splitlines() if "[BUDŻET] 32;9;" in w]
    assert wiersze, "krok kontroli nie ma juz wiersza atrapy o obsadzie dziewieciu"
    for wiersz in wiersze:
        kolumny = wiersz.split("[BUDŻET] 32;9;", 1)[1].split(";")
        us = kolumny[6]
        try:
            wartosc = float(us)
        except ValueError:
            continue  # podstawienie z powloki — wartosc jest wyliczana, o to chodzi
        assert wartosc > prog, (
            "atrapa odmowy czasowej w kroku CI niesie literal %s us przy progu "
            "%.3f us, czyli MIESCI SIE w progu — kontrola negatywna zaczerwieni sie "
            "zdaniem o pomiarze, ktory wolniejszy nie jest" % (us, prog))


# --- 08.09.2026: granica rozstepu podniesiona na 100 %, kompensata w ostrzezeniu -----

#: Rozstepy TRZECH kolejnych przebiegow kalibracyjnych 06.09.2026 (raport §3, wklejone
#: wiersze `[BUDŻET]`). `max` z tej trojki to najgorzej uwarunkowany przebieg, NA
#: KTORYM ZMIERZONO PROG — i to jest cala podstawa poziomu ostrzezenia.
ROZSTEPY_KALIBRACJI = (17.0, 13.1, 22.5)

#: Rozstepy PIECIU przebiegow tej bramki na kontenerze sesji 08.09.2026, ta sama tresc
#: kodu, koszt kroku odpowiednio 3,803 / 3,810 / 3,736 / 4,040 / 3,871 us — WSZYSTKIE
#: kodem 0, czyli piec pomiarow ZIELONYCH.
#: Zmierzone przy tej zmianie i wazne z dwoch powodow naraz:
#: (1) `max` = 47,5 % jest ZIELONYM pomiarem lezacym 2,5 pp pod stara granica 50 %,
#:     czyli stara granica byla o jedno wahanie od orzeczenia niemierzalnosci
#:     o przebiegu, ktory zmierzyl 3,810 us — to jest pomiarowy argument ZA decyzja
#:     wlasciciela i dlatego stoi w kodzie, a nie tylko w raporcie;
#: (2) `max - min` = 32,9 pp mowi, ze sama kolumna rozstepu waha sie o tyle przy
#:     NIEZMIENNEJ tresci kodu i NIEZMIENNEJ maszynie — wiec marginesu granicy pod
#:     115,9 % NIE da sie oprzec na wahaniu rozstepu: zadanie 32,9 pp marginesu
#:     spycha granice na 83,0 %, czyli pod zaobserwowane 84,0 %. Margines jest
#:     dlatego oparty na DRUGIM POMIARZE (102,6 %), a nie na wahaniu.
ROZSTEPY_KONTENERA_08_09 = (24.9, 47.5, 14.6, 19.0, 18.0)

#: Rozstep, przy ktorym padl JEDYNY pomiar niemierzalny majacy PARE: 16,022 us na
#: `woogitsu-host-08` przy dwunastu jobach naraz, wobec 4,213-4,364 us na tej samej
#: tresci kodu na maszynie niezajetej (07.09.2026, reports/rozstep-budzetu-kroku.md).
#: To jest gorne ograniczenie granicy.
NIEMIERZALNY_ROZSTEP = 115.9

#: Drugi rozstep powyzej 100 % zapisany w tym repozytorium: 102,6 % przy JEDNYM pull
#: requescie w puli (08.09.2026, job 101900177486, docs/TASKS.md 6.D43). Pary nie ma,
#: wiec dowodem niemierzalnosci nie jest — ale jest liczba, ktora bramka widziala,
#: i granica stojaca nad nia przestalaby ja odrzucac.
NIEMIERZALNY_ROZSTEP_DRUGI = 102.6

#: Atrapa odmowy CZASOWEJ przy pomiarze SLABO UWARUNKOWANYM: 95,0 % lezy miedzy
#: 84,0 % i 102,6 % zmierzonymi na obciazonej puli (6.D43), wiec nie jest liczba
#: wymyslona, a przy granicy 100 % jest MIERZALNA — czyli trafia do porownania
#: z progiem i to jest caly sens tego wejscia.
SLABO_UWARUNKOWANY_PONAD_PROGIEM = ZIELONY.replace(
    ";17.0;3.772;1.01;0.05", ";95.0;16.000;1.00;0.19")


def test_odmowa_czasowa_przy_SLABYM_UWARUNKOWANIU_NAZYWA_je():
    """Kompensata do podniesienia granicy z 50 % na 100 % — i sedno tej zmiany.

    Podniesienie `spread_pct_max` znaczy, ze WIECEJ pomiarow jest porownywanych
    z progiem czasu. Pomiar o rozstepie 95 % byl do 08.09.2026 niemierzalnoscia
    (kod 3), a dzis jest odmowa czasowa (kod 1) — czyli zdaniem „rdzen zwolnil"
    o pomiarze, ktory mowi wylacznie o obciazeniu maszyny. To jest dokladnie to
    klamstwo, ktore naprawila 6.D41, wpuszczone z powrotem przez szersza granice.

    Odwrocic tego nie wolno, bo szersza granica jest decyzja wlasciciela. Ten test
    zada minimum, ktorego nie sprawdzalo NIC: zeby odmowa nazwala slabe uwarunkowanie
    i podala rozstep, wiec zeby czytajacy log nie dostal diagnozy „szukaj regresu
    w kodzie" bez ostrzezenia, ze pomiar jej nie uzasadnia.
    """
    config = _config()
    rozstep = float(
        SLABO_UWARUNKOWANY_PONAD_PROGIEM.strip().splitlines()[-1].split(";")[7])
    assert rozstep == 95.0, rozstep
    assert rozstep <= config["spread_pct_max"], (
        "atrapa o rozstepie %.1f %% jest przy granicy %.1f %% NIEMIERZALNA, wiec ten "
        "test pyta o co innego, niz mysli — odmowy czasowej w ogole nie bedzie"
        % (rozstep, config["spread_pct_max"]))
    assert rozstep > config["spread_pct_warn"], (
        "atrapa o rozstepie %.1f %% nie przekracza poziomu ostrzezenia %.1f %%"
        % (rozstep, config["spread_pct_warn"]))

    ok, problems = gate.verdict(config, SLABO_UWARUNKOWANY_PONAD_PROGIEM)
    assert not ok, problems
    czasowe = [p for p in problems if "przekracza prog" in p]
    assert czasowe, (
        "pomiar 16,000 us przy progu %.3f us nie dal odmowy czasowej: %s"
        % (config["microseconds_per_step_max"], problems))
    for problem in czasowe:
        assert "SLABO UWARUNKOWANY" in problem, (
            "odmowa czasowa przy rozstepie %.1f %% nie nazywa slabego uwarunkowania: %s"
            % (rozstep, problem))
        assert "95.0" in problem, (
            "odmowa nie podaje rozstepu, wiec czytajacy nie wie, jak slaby jest "
            "ten pomiar: %s" % problem)


def test_odmowa_czasowa_przy_MOCNYM_uwarunkowaniu_NIE_dokleja_ostrzezenia():
    """Druga strona tej samej kompensaty — bez niej pierwsza jest do oszukania.

    Zdanie o slabym uwarunkowaniu doklejone do KAZDEJ odmowy czasowej przechodziloby
    test powyzej i nie mowiloby nic: 6.D27 mowi, ze bramka zapalajaca sie na tekscie
    poprawnym zostaje wylaczona, a to samo dotyczy ostrzezenia doklejanego wszedzie.
    Atrapa WOLNY niesie rozstep 17,0 %, czyli ponizej poziomu ostrzezenia — pomiar
    o takim rozstepie byl historycznie ZIELONY i jego odmowa mowi o kodzie.
    """
    config = _config()
    rozstep = float(WOLNY.strip().splitlines()[-1].split(";")[7])
    assert rozstep <= config["spread_pct_warn"], (
        "atrapa WOLNY niesie rozstep %.1f %% powyzej poziomu ostrzezenia %.1f %%, "
        "wiec ten test nie umie juz sprawdzic drugiej strony warunku"
        % (rozstep, config["spread_pct_warn"]))
    ok, problems = gate.verdict(config, WOLNY)
    assert not ok
    assert any("przekracza prog" in p for p in problems), problems
    assert not any("SLABO UWARUNKOWANY" in p for p in problems), (
        "ostrzezenie o slabym uwarunkowaniu doklejone do odmowy przy rozstepie "
        "%.1f %% — czyli doklejane do wszystkiego, wiec nie znaczace nic: %s"
        % (rozstep, problems))


def test_poziom_ostrzezenia_lezy_MIEDZY_KALIBRACJA_a_ODRZUCONYM_pomiarem():
    """Poziom WYPROWADZONY z pomiarow, nie wpisany z reki — w obie strony.

    Od dolu: nie moze byc nizszy od najgorzej uwarunkowanego z trzech przebiegow,
    NA KTORYCH ZMIERZONO PROG (22,5 %, kalibracja 06.09.2026) — poziom ponizej tej
    liczby oznaczalby jako slabo uwarunkowane pomiary co najmniej tak dobre jak te,
    z ktorych prog pochodzi. Poziom NIE jest granica miedzy zielonym a czerwonym
    i ten test tego nie twierdzi: przebiegi zielone o rozstepie 24,9 i 47,5 % sa
    zmierzone (`ROZSTEPY_KONTENERA_08_09`), wiec znacznik jest adnotacja o jakosci
    pomiaru, a nie werdyktem o kodzie.

    Od gory: musi lezec PONIZEJ 33,9 % — rozstepu, przy ktorym padl pomiar 9,572 us
    stanowiacy dolne ograniczenie progu. Ten pomiar jest odmowa czasowa, ktorej sesja
    z 08.09.2026 nie umiala odroznic od regresu w kodzie; poziom powyzej niego
    zostawilby ja bez oznaczenia, czyli kompensata omijalaby wlasnie ten przypadek,
    dla ktorego powstala.
    """
    config = _config()
    assert "spread_pct_warn" in config, (
        "poziom ostrzezenia zniknal z pliku progu — odmowa czasowa przestaje nazywac "
        "slabe uwarunkowanie, a granica 100 % zostaje bez kompensaty")
    poziom = config["spread_pct_warn"]
    z_atrapy = float(ZIELONY.strip().splitlines()[-1].split(";")[7])
    assert poziom >= max(ROZSTEPY_KALIBRACJI), (
        "poziom ostrzezenia %.1f %% lezy PONIZEJ najgorzej uwarunkowanego przebiegu "
        "kalibracyjnego (%.1f %%), na ktorym zmierzono prog — ostrzezenie trafialoby "
        "do odmow rownie dobrze uwarunkowanych jak podstawa progu"
        % (poziom, max(ROZSTEPY_KALIBRACJI)))
    assert poziom >= z_atrapy, (poziom, z_atrapy)
    assert poziom < ODRZUCONY_MIERZALNY_ROZSTEP, (
        "poziom ostrzezenia %.1f %% nie oznaczylby pomiaru przy %.1f %% (9,572 us), "
        "czyli tej odmowy, ktora ta kompensata ma nazywac"
        % (poziom, ODRZUCONY_MIERZALNY_ROZSTEP))
    assert poziom < config["spread_pct_max"], (
        "poziom ostrzezenia %.1f %% lezy na granicy niemierzalnosci %.1f %% albo nad "
        "nia — wtedy nie ostrzega przed niczym, bo powyzej niego nie ma odmow czasowych"
        % (poziom, config["spread_pct_max"]))


def test_granica_rozstepu_jest_ZABOKSOWANA_miedzy_pomiarami_z_OBU_stron():
    """Sam MARGINES jest tu asercja, a nie zaufaniem — i do 08.09.2026 nie bylo go wcale.

    `test_granica_rozstepu_jest_POWYZEJ_udokumentowanych_pomiarow_zielonych` zada
    `granica < 115,9`, czyli zabrania marginesu ZEROWEGO albo ujemnego. Przy granicy
    50 % to wystarczalo, bo do liczby 115,9 bylo daleko. Decyzja wlasciciela
    z 08.09.2026 przesuwa granice MOZLIWIE BLISKO 115,9 %, wiec samo „ponizej" przestaje
    byc warunkiem o czymkolwiek: granica 115,8 % spelnia go, a odrzuca zaobserwowana
    niemierzalnosc o wlos.

    Margines NIE jest tu liczba dobrana ani wahaniem rozstepu — i to jest wynik pomiaru,
    nie wygoda. Wahanie sie nie nadaje: cztery przebiegi tej bramki na kontenerze
    08.09.2026 dały rozstepy 14,6-47,5 % przy NIEZMIENNEJ tresci kodu, czyli 32,9 pp,
    a granica o 32,9 pp pod 115,9 % to 83,0 % — PONIZEJ zaobserwowanego 84,0 %, czyli
    ciasniej, niz mowi decyzja. Gorne ograniczenie jest wiec wziete z DRUGIEGO POMIARU:
    102,6 % (6.D43, job 101900177486, jeden pull request w puli). Pary ten pomiar nie
    ma, wiec dowodem niemierzalnosci nie jest — ale jest liczba, ktora ta bramka
    widziala, i granica nad nia przestalaby ja odrzucac, czego nikt nie zapisal jako
    decyzji. Margines pod 115,9 % wychodzi z tego sam i jest tu wypisany liczba.

    Od dolu doszlo ograniczenie, ktorego nie bylo: 47,5 % to rozstep przebiegu
    ZIELONEGO (3,810 us, kod 0) zmierzonego przy tej zmianie. Granica ponizej niego
    orzekalaby niemierzalnosc o pomiarze, ktory zmierzyl koszt kroku poprawnie —
    czyli 6.D27: bramka zapalajaca sie na tekscie poprawnym zostaje wylaczona. Stara
    granica 50 % spelniala to z zapasem 2,5 pp, o czym nikt nie wiedzial, bo tego
    rozstepu jeszcze nie zmierzono.
    """
    granica = _config()["spread_pct_max"]
    zielony_najgorszy = max(ROZSTEPY_KONTENERA_08_09)
    assert granica > zielony_najgorszy, (
        "granica %.1f %% orzekalaby NIEMIERZALNOSC o przebiegu zielonym o rozstepie "
        "%.1f %% (3,810 us, kod 0, kontener 08.09.2026)"
        % (granica, zielony_najgorszy))
    assert granica < NIEMIERZALNY_ROZSTEP_DRUGI, (
        "granica %.1f %% przepuszczalaby jako MIERZALNY rozstep %.1f %% zmierzony "
        "08.09.2026 na obciazonej puli (6.D43, job 101900177486)"
        % (granica, NIEMIERZALNY_ROZSTEP_DRUGI))
    # Ograniczenie z 102,6 % wymusza margines >= 13,3 pp, wiec ta asercja jest dzis
    # slabsza. Zostaje mimo to, i to jest wybor: 102,6 % PARY nie ma, wiec kiedys moze
    # zostac wycofane jako podstawa — a wtedy podloga na sam margines jest ostatnim,
    # co stoi miedzy granica a liczba 115,9 %, ktora bramka juz widziala.
    margines = NIEMIERZALNY_ROZSTEP - granica
    assert margines > 0.0, (
        "granica %.1f %% nie zostawia marginesu pod zaobserwowanym pomiarem "
        "niemierzalnym %.1f %% (margines %.1f pp)"
        % (granica, NIEMIERZALNY_ROZSTEP, margines))
