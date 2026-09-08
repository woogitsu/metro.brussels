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
import sys

sys.path.insert(0, os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "ci"))

import assert_linecore_budget as gate  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "sim-tests.yml")

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
    rozjechalyby sie po cichu, a `$comment_spread_pct_max` wprost zapowiada, ze granica
    ma byc zaciesniana.
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
