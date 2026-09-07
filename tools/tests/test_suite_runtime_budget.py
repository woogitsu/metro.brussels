#!/usr/bin/env python3
"""6.D11: próg czasu ściany dla `python3 tools/tests/test_all.py` w CI.

**Dlaczego próg NIE siedzi w `test_all.py`.** Kod wyjścia tamtego pliku czyta
`tools/tests/mutation_sweep.py` (`run_suite`, regex `SUMMARY`): mutacja jest uznana
za PRZEŻYTĄ dokładnie wtedy, gdy linia `N/M przeszło` mówi `N == M` **i** kod wyjścia
jest zerowy. Gdyby `main()` w `test_all.py` zwracał 1 również przy przekroczeniu
czasu, zwykłe spowolnienie współdzielonej maszyny — a ta jest współdzielona, patrz
niżej — zamieniłoby się w falę fałszywych „zabić" mutacyjnych, tej samej rodziny co
`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`, tylko odwróconej: nie fałszywe
przeżycie, tylko fałszywa śmierć. Bramka czasu żyje więc w kroku CI (`.github/
workflows/python-tests.yml`), PO zakończeniu procesu — `test_all.py` sam wypisuje
tylko czas, nie ocenia go.

**Skąd próg.** Zmierzone 06.09.2026 na commicie `045730bd639c771d59b6d3b876c4d390d85f16ad`,
cztery przebiegi CAŁEGO procesu `python3 tools/tests/test_all.py` z rzędu, bez ŻADNEJ
zmiany kodu i przy stałych 1709 testach: **66,20 / 68,45 / 68,96 / 77,04 s**
(`time.perf_counter()` od uruchomienia procesu do jego zakończenia, mierzone z
zewnątrz — nie licznik wewnętrzny `test_all.py`, który liczy tylko samą pętlę testów
i wypada o ok. 1-2 s niżej, bo pomija import i odkrywanie modułów). Maszyna jest
KONTENEREM DZIELONYM z innymi sesjami agenta — `ps aux` w trakcie pomiaru pokazywał
równoległy `dotnet build` i proces Godota z sąsiedniego katalogu roboczego — stąd
rozrzut 10,84 s na średniej 70,16 s (15,45 % względem średniej, 16,37 % względem
najniższego pomiaru) przy tym samym kodzie i tej samej liczbie testów. Pełna tabela
per moduł: `reports/test-all-runtime-gate.md`.

**Skąd mnożnik.** `SUITE_RUNTIME_BUDGET_S` to NIE najwyższy zmierzony czas — to
najwyższy zmierzony czas razy margines, bo próg ma przeżyć DWIE rzeczy, których żadna
sesja nie zmierzyła: (1) maszyna właściciela (`woogitsu`, `CLAUDE.md` §9) chodzi gdzie
indziej, z nieznaną prędkością i własnym wzorcem obciążenia; (2) zestaw rośnie z każdym
zadaniem — o kilkadziesiąt testów dziennie — a próg dostrojony tuż nad dzisiejszym
maksimum wymagałby przeliczania co kilka dni, czyli przestałby być bramką, a stałby się
rytuałem.

**Ile ten margines wynosi, ten plik już nie twierdzi prozą — LICZY.** Ten akapit jest
przepisany, a nie dopisany obok (6.D26). Poprzednia wersja podawała mnożnik **wprost
w tekście**, a komentarz przy teście marginesu podawał **drugi, inny** — oba wyliczone
kiedyś wobec `MEASURED_MAX_WALL_S` wpisanego z ręki 05.09.2026, oba prawdziwe tamtego
dnia i oba **przestały być prawdziwe, nie zmieniając ani znaku**, gdy 07.09.2026 ten sam
zestaw zmierzył 107,33 s. Te dwie liczby stoją teraz w
`reports/zapis-czasu-zestawu.md`, gdzie są historią, a nie w kodzie, gdzie wyglądałyby
na obowiązujące. Nic tego nie zgłosiło, bo margines liczył się wobec
zapisanej liczby, nie wobec czegokolwiek zmierzonego później — a to jest dokładnie ten
kształt usterki, którego pilnuje `test_report_claims.py` dla stałych cytowanych
w raportach, tylko schowany we własnym docstringu bramki.

Teraz maksimum jest wyprowadzane z listy `POMIARY`, margines stoi w `MARGIN` jako
działanie, a osobny test pilnuje, żeby żadna liczba w tej prozie nie rozjechała się
z liczbą w kodzie. Próg 150,0 zostaje **nietknięty**: jego zmiana jest decyzją
o czułości bramki, a nie skutkiem ubocznym poprawiania zapisu pomiaru.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "python-tests.yml")

#: Przebiegi, które KTOŚ NAPRAWDĘ ZMIERZYŁ: (data, sekundy, modułów, na czym).
#:
#: **Lista, a nie jedna liczba — i to jest poprawka na konkretną usterkę (6.D26).**
#: Do tej pozycji stała `MEASURED_MAX_WALL_S = 77.04` była wpisana z ręki jako „najwyższy
#: z czterech przebiegów" jednej, minionej sesji. Liczba wpisana raz opisuje dzień,
#: w którym ją wpisano; 07.09.2026 ten sam zestaw dawał **107,33 s**, czyli o 39 %
#: więcej — a nic tego nie zgłaszało, bo margines liczył się wobec zapisanych 77,04,
#: nie wobec czegokolwiek zmierzonego później. Komentarz przy teście marginesu podawał
#: tę liczbę wprost i **przestał być prawdą, nie zmieniając ani znaku**; obie
#: nieaktualne wartości stoją teraz w `reports/zapis-czasu-zestawu.md`.
#:
#: Teraz maksimum jest WYPROWADZANE z tej listy, więc dopisanie przebiegu automatycznie
#: zacieśnia raportowany margines i nie da się mieć jednego bez drugiego. Dat nie
#: przelicza się ani nie nadpisuje: 77,04 zostaje jako pomiar swojego dnia.
POMIARY = (
    ("2026-09-05", 77.04, None,
     "najwyższy z czterech przebiegów tamtej sesji; kontener DZIELONY, `ps aux` "
     "pokazywał równoległy `dotnet build` i proces Godota"),
    ("2026-09-07", 76.518, 93,
     "po 6.B30 (pamięć na układ peronów), host spokojny"),
    ("2026-09-07", 102.122, 93,
     "ten sam kod, host pod obciążeniem: `test_station_layout` mierzył wtedy 34,9 s "
     "wobec 22,7 s godzinę wcześniej — 1,54x rozrzutu na jednym module, "
     "potwierdzone identycznym pomiarem w drzewie sprzed 6.A18"),
    ("2026-09-07", 83.083, 95,
     "po 6.A20, dwa moduły bramek więcej"),
    ("2026-09-07", 107.331, 95,
     "to samo drzewo, host pod obciążeniem — NAJWYŻSZY zmierzony do dziś"),
)

#: Najwyższy ZMIERZONY przebieg, wyprowadzony z `POMIARY`. Stała osobna od
#: `SUITE_RUNTIME_BUDGET_S`, żeby dało się sprawdzić SAM margines (test niżej), a nie
#: tylko to, że próg jest jakąś liczbą dodatnią.
MEASURED_MAX_WALL_S = max(sekundy for _data, sekundy, _moduly, _gdzie in POMIARY)

#: Próg bramki CI. Czytany z TEGO pliku przez krok „Run tool tests" w
#: `python-tests.yml` (`python3 -c "... import test_suite_runtime_budget ..."`) —
#: jedno miejsce prawdy, nie liczba wpisana w YAML z ręki.
SUITE_RUNTIME_BUDGET_S = 150.0

#: Margines progu nad najwyższym zmierzonym przebiegiem — LICZONY, nie opisany prozą.
#: Poprzednia wersja nosiła tę liczbę w komentarzu, wpisaną z ręki — i to właśnie
#: zdanie zestarzało się bez śladu, bo nic nie łączyło go z liczbami obok. Ile wtedy
#: podawało, stoi w `reports/zapis-czasu-zestawu.md`, gdzie jest historią.
MARGIN = SUITE_RUNTIME_BUDGET_S / MEASURED_MAX_WALL_S


def over_budget(elapsed_s, budget_s=SUITE_RUNTIME_BUDGET_S):
    """Czy zmierzony czas ściany przekracza próg. Równość progu NIE jest przekroczeniem —

    ta sama konwencja, co gdzie indziej w tym repo dla granic włącznie (np.
    `PARALLEL_M jest granicą włącznie` w `test_report_claims.py`).
    """
    return elapsed_s > budget_s


def _workflow_text():
    with open(WORKFLOW, encoding="utf-8") as handle:
        return handle.read()


def test_budget_constant_is_a_sane_positive_number():
    assert isinstance(SUITE_RUNTIME_BUDGET_S, float)
    assert 30.0 < SUITE_RUNTIME_BUDGET_S < 900.0, SUITE_RUNTIME_BUDGET_S


def test_budget_stays_above_the_measured_maximum_with_a_real_margin():
    """Bramka na samą bramkę.

    Bez tego testu ktoś mógłby obniżyć `SUITE_RUNTIME_BUDGET_S` poniżej
    `MEASURED_MAX_WALL_S` bez żadnego ostrzeżenia — a próg niższy niż to, co
    już zostało zmierzone na spokojnej maszynie, zapala się na czerwono od
    samego sąsiedztwa na runnerze, bez żadnego regresu w kodzie.
    """
    assert SUITE_RUNTIME_BUDGET_S > MEASURED_MAX_WALL_S, (
        SUITE_RUNTIME_BUDGET_S, MEASURED_MAX_WALL_S)
    # Test żąda tylko, żeby margines NIE stopniał do czegoś ciasnego przy przyszłej
    # edycji — próg 1.2 łapie „obniżono do 78". Ile margines wynosi DZIŚ, mówi `MARGIN`,
    # liczone z `POMIARY`; wpisanie tu drugiej liczby z ręki byłoby powtórzeniem błędu,
    # który naprawiło 6.D26.
    assert MARGIN > 1.2, (MARGIN, SUITE_RUNTIME_BUDGET_S, MEASURED_MAX_WALL_S)


def test_every_recorded_run_says_when_and_on_what_it_was_measured():
    """Pomiar bez daty i bez kontekstu jest nierozstrzygalny.

    O to poszlo w 6.D26: `MEASURED_MAX_WALL_S = 77.04` nie mowilo ANI kiedy powstalo,
    ANI ze host jest kontenerem dzielonym — wiec czytajacy nie mial jak odroznic
    „zestaw przyspieszyl" od „tamtego dnia maszyna byla spokojna". Kazdy wpis musi
    nosic jedno i drugie.
    """
    assert len(POMIARY) >= 2, (
        "jeden pomiar nie pozwala odroznic regresu od rozrzutu hosta — po to jest lista")
    for data, sekundy, moduly, gdzie in POMIARY:
        assert re.fullmatch(r"20\d\d-\d\d-\d\d", data), data
        assert isinstance(sekundy, float) and 10.0 < sekundy < 900.0, (data, sekundy)
        assert moduly is None or isinstance(moduly, int), (data, moduly)
        assert len(gdzie) > 25, (
            "kontekst ma mowic, na czym i w jakich warunkach: " + repr((data, gdzie)))


def test_the_recorded_maximum_is_derived_not_typed_in():
    """Maksimum wyprowadzone, nie wpisane — inaczej dopisanie pomiaru nie zmienia
    niczego i lista staje sie ozdoba obok liczby, ktora nadal rzadzi."""
    assert MEASURED_MAX_WALL_S == max(s for _d, s, _m, _g in POMIARY)
    with open(__file__, encoding="utf-8") as uchwyt:
        source = uchwyt.read()
    assert not re.search(r"^MEASURED_MAX_WALL_S\s*=\s*[\d.]+\s*$", source, re.M), (
        "maksimum wpisane z reki zamiast wyprowadzone z POMIARY")


#: Zdanie o marginesie i mnoznik, ktory sie w nim styka ze znacznikiem mnozenia.
#: Dwa wzorce, nie jeden, i oba wyszly z prob na tym pliku — patrz docstring testu.
#: Kropka jest przepuszczana TYLKO wtedy, gdy stoi przed cyfra — inaczej okno urywa
#: sie na kropce dziesietnej i `1.40x` widzi jako `1`. Wyszlo z proby: kontrola
#: narzedzia zglosila „detektor nie widzi zdania, ktore ma widziec" na zdaniu
#: zbudowanym przez `%.2f`, czyli z kropka, a nie z przecinkiem.
_OKOLICA_MARGINESU = re.compile(
    r"(?:margines\w*|mnoznik\w*|mnożnik\w*)(?:[^.\n]|\.(?=\d)){0,80}", re.IGNORECASE)
_MNOZNIK = re.compile(r"(?:x\s*(\d+(?:[.,]\d+)?)\b"
                      r"|\b(\d+(?:[.,]\d+)?)\s*[x×]"
                      r"|\brazy\s+(\d+(?:[.,]\d+)?))")


def mnozniki_w(text):
    """Mnozniki podane w zdaniach o marginesie, jako liczby. Pusta lista = zadnych."""
    znalezione = []
    for fragment in _OKOLICA_MARGINESU.finditer(text):
        for trafienie in _MNOZNIK.finditer(fragment.group(0)):
            surowa = next(g for g in trafienie.groups() if g)
            znalezione.append(float(surowa.replace(",", ".")))
    return znalezione


def test_the_prose_does_not_quote_a_margin_that_the_numbers_do_not_give():
    """Sedno 6.D26. Proza tego pliku nie ma prawa podawac MNOZNIKA, ktorego nie daja
    stale obok — bo wlasnie takie zdanie zestarzalo sie tu bez sladu.

    Liczba liczy sie jako mnoznik dopiero wtedy, gdy **styka sie ze znacznikiem**
    mnozenia (`x2`, `1,4x`, `1,95×`, `razy 2`) i stoi w zdaniu o marginesie. Dwa
    warunki, a nie jeden, i oba wyszly z prob na tym pliku:
    - bez znacznika bramka brala za mnoznik KAZDA liczbe obok slowa „margines" —
      zapalila sie na `77,04`, czyli na POMIARZE w zdaniu o tym, wobec czego margines
      sie liczyl;
    - bez warunku na „margines" brala kazdy mnoznik w pliku, a plik mowi tez o `1,54x`
      rozrzutu hosta na jednym module, ktory z marginesem progu nie ma nic wspolnego.

    **Test sprawdza NARZEDZIE, nie tylko dzisiejszy tekst** — i to tez wyszlo z proby:
    po wycieciu wlasnego docstringa ze skanowania w pliku nie zostalo ANI JEDNEGO
    zdania z mnoznikiem, wiec petla nie miala po czym iterowac i test przeszedl
    **bez ani jednej asercji**. Zlapala to bramka asercji z #139. Wersja nizej ma
    asercje zawsze: sprawdza, ze detektor lapie podstawione zdanie nieaktualne, ze
    przepuszcza zdanie zgodne z `MARGIN`, ze nie bierze pomiaru za mnoznik i ze nie
    wchodzi w mnozniki spoza zdan o marginesie.

    **Czego ta bramka NIE lapie, swiadomie:** zdania „margines wynosi 1,40" bez
    znacznika. Wezsze kryterium przepuszcza taki zapis, szersze zapala sie na kazdej
    liczbie w okolicy — a bramka, ktora swieci na poprawnym tekscie, zostaje wylaczona.
    Zapis mnoznikiem jest w tym repozytorium konwencja, wiec kryterium trafia w to, jak
    te zdania naprawde sie pisze.
    """
    with open(__file__, encoding="utf-8") as uchwyt:
        source = uchwyt.read()
    # Wlasny test jest wyciety ze skanowania, i to nie jest wyjatek dla wygody: jego
    # docstring OPISUJE skladnie, ktora bramka rozpoznaje, wiec musi te mnozniki
    # wymienic jako przyklady. Bramka skanujaca sama siebie zapalalaby sie na wlasnej
    # dokumentacji — i zostalaby wylaczona, nie poprawiona.
    granica = source.index("#: Zdanie o marginesie i mnoznik")
    for podana in mnozniki_w(source[:granica]):
        assert abs(podana - MARGIN) < 0.005, (
            "proza podaje mnoznik %s, a MARGIN = %.4f" % (podana, MARGIN))

    # Kontrola narzedzia — wykonywana za kazdym przebiegiem, nie raz przy pisaniu.
    nieaktualne = "Margines jest x2 nad najwyzszym zmierzonym przebiegiem."
    assert mnozniki_w(nieaktualne) == [2.0], mnozniki_w(nieaktualne)
    zgodne = "Margines wynosi %.2fx nad najwyzszym zmierzonym przebiegiem." % MARGIN
    for podana in mnozniki_w(zgodne):
        assert abs(podana - MARGIN) < 0.005, (podana, MARGIN)
    assert mnozniki_w(zgodne), "detektor nie widzi zdania, ktore ma widziec"
    pomiar = "Margines liczyl sie wobec zapisanych 77,04 sekundy."
    assert mnozniki_w(pomiar) == [], (
        "pomiar wziety za mnoznik: " + repr(mnozniki_w(pomiar)))
    obok = "Rozrzut hosta na jednym module to 1,54x przy tym samym kodzie."
    assert mnozniki_w(obok) == [], (
        "mnoznik spoza zdania o marginesie: " + repr(mnozniki_w(obok)))


def test_over_budget_boundary_is_strict_greater_than():
    assert over_budget(SUITE_RUNTIME_BUDGET_S) is False
    assert over_budget(SUITE_RUNTIME_BUDGET_S - 0.001) is False
    assert over_budget(SUITE_RUNTIME_BUDGET_S + 0.001) is True


def test_over_budget_default_argument_tracks_the_shared_constant():
    """Wersja bez podanego `budget_s` musi patrzeć na TĘ SAMĄ stałą, nie na kopię."""
    assert over_budget(SUITE_RUNTIME_BUDGET_S + 1.0) is True
    assert over_budget(SUITE_RUNTIME_BUDGET_S - 1.0) is False


def test_ci_gate_step_reads_this_files_constant_not_a_second_copy():
    """Krok YAML musi czytać `SUITE_RUNTIME_BUDGET_S` STĄD, nie nosić drugiej liczby.

    Dwa źródła progu rozjeżdżają się bezszelestnie przy pierwszej edycji jednego
    z nich — dokładnie klasa usterki, którą `test_report_claims.py` łapie dla
    stałych cytowanych w `reports/`. YAML nie jest raportem, więc tamta bramka
    go nie widzi; ten test jest jej odpowiednikiem dla workflow.
    """
    text = _workflow_text()
    assert "tools/tests/test_suite_runtime_budget.py" in text, text
    assert "SUITE_RUNTIME_BUDGET_S" in text, text
    # Żaden inny fragment kroku nie wpisuje progu jako gołej liczby przypisanej do
    # zmiennej „budget" z ręki — to złapałoby drugą, ukrytą kopię wartości.
    assert not re.search(r"budget\s*=\s*[\"']?\d", text, re.IGNORECASE), text


def test_ci_gate_step_is_a_comparison_that_can_exit_non_zero():
    """Krok o tej nazwie musi umieć wywalić joba, nie tylko wypisać liczby.

    Ta sama klasa kontroli, co `test_ci_reference_parity_step_is_a_gate_not_a_print`
    w `test_ci_workflows.py` (zarezerwowanym dla innej pozycji) — napisana tu, żeby
    nie dotykać cudzego pliku.
    """
    text = _workflow_text()
    step_start = text.index("Run tool tests")
    step = text[step_start:text.index("\n      - name:", step_start)]
    assert "SUITE_RUNTIME_BUDGET_S" in step, step
    assert re.search(r"exit\s+1\b", step), step
    assert "set -euo pipefail" in step, (
        "bez tego krok kontynuowałby po awarii test_all.py aż do własnego "
        "porownania czasu i mógłby zameldować sukces mimo nieudanych testów")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
