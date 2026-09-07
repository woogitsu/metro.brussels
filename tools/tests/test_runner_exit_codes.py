#!/usr/bin/env python3
"""Kod 2 znaczy „nie wiem, co uruchomic" — i nic wiecej.

**Skad ta bramka.** Do 06.09.2026 `Sim.Runner` mial trzy miejsca zwracajace 2: nieznane
polecenie, wywolanie bez ani jednego argumentu i `compare` bez dwoch plikow. Dwa
pierwsze naleza do jednej rodziny („nie wiadomo, co uruchomic"), trzecie do zupelnie
innej („polecenie znane, argumenty zle") — a ta druga rodzina we wszystkich pozostalych
odmowach konczy sie kodem 1, przez wspolny handler wyjatkow.

Cztery pozycje — 6.A10 (#302), 6.A11 (#307), 6.A13 (#313) i 6.D20 (#312) — nazwaly te
niespojnosc i **swiadomie jej nie ruszyly**, przybijajac stan testem: wybor miedzy 1 a 2
nie nalezal do pozycji, ktora ma opisac zastane zachowanie. Wlasciciel wybral 06.09.2026:
kazda odmowa argumentowa = 1, a 2 zostaje wylacznie dla dwoch pierwszych sciezek.

**Dlaczego to jest bramka, a nie tylko test C#.** Test C# sprawdza kod wyjscia jednego
wywolania. Ta bramka czyta `Program.cs` jako TEKST i pilnuje, ze `return 2` nie pojawi
sie w trzecim miejscu — bo trzecie miejsce nie zlamie zadnego istniejacego testu, dopoki
nikt nie napisze mu wlasnego. Ujednolicenie, ktorego nikt nie pilnuje, rozjezdza sie przy
pierwszym nowym poleceniu.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")

#: Dwie sciezki, ktorym kod 2 przysluguje — obie znacza „nie wiem, co uruchomic".
#: Nazwy sa fragmentami kodu wokol `return 2`, nie numerami wierszy: numer starzeje
#: sie przy pierwszej wstawce, fragment nie.
DOZWOLONE = (
    "if (args.Length == 0)",          # wywolanie bez ani jednego argumentu
    "nieznane polecenie:",            # Unknown(command)
)


def _source():
    with open(PROGRAM, encoding="utf-8") as handle:
        return handle.read()


def _return_two_sites(source):
    """Fragmenty kodu poprzedzajace kazde `return 2;` — po jednym na wystapienie."""
    sites = []
    for match in re.finditer(r"return 2;", source):
        start = max(0, match.start() - 400)
        sites.append(source[start:match.start()])
    return sites


def test_exit_code_two_only_means_we_do_not_know_what_to_run():
    sites = _return_two_sites(_source())
    assert sites, "w Program.cs nie ma ani jednego `return 2` — kod 2 zniknal calkiem"
    for site in sites:
        assert any(marker in site for marker in DOZWOLONE), (
            "`return 2` w miejscu spoza dwoch dozwolonych sciezek. Kod 2 znaczy "
            "nie wiem, co uruchomic; odmowa argumentowa ma konczyc sie kodem 1 "
            "przez wspolny handler. Kontekst: ..." + site[-200:])


def test_both_allowed_paths_are_still_there():
    """Drugi kierunek: gdyby ktos zamienil na 1 takze te dwie sciezki, powyzszy test
    przeszedlby na pustym zbiorze. Kod 2 ma ISTNIEC i miec dokladnie te dwa powody."""
    sites = _return_two_sites(_source())
    assert len(sites) == len(DOZWOLONE), (
        "sciezek z kodem 2 jest %d, a powody sa dwa" % len(sites))
    for marker in DOZWOLONE:
        assert any(marker in site for site in sites), (
            "zniknela sciezka kodu 2: " + marker)


def _bez_komentarzy(source):
    """`Program.cs` bez wierszy komentarza — wzmianka w komentarzu nie jest kodem.

    Potrzebne od 6.A27: akapity wyjasniajace, DLACZEGO odmowa nie uzywa
    `Console.Error` + `return 1`, same te napisy zawieraja. Bramka zapalajaca sie na
    tekscie, ktory ja wyjasnia, zostaje wylaczona, nie naprawiona (6.D27, 6.D30).
    """
    return "\n".join(
        line for line in source.splitlines()
        if not line.strip().startswith(("//", "///")))


def _cialo_compare(source):
    at = source.index("private static int Compare(")
    return source[at:source.index("\n    private static", at + 10)]


def test_compare_refuses_through_the_common_handler():
    """Kazda odmowa `compare` idzie wspolnym handlerem — LICZONA, nie „choc jedna".

    **Ta asercja jest PRZEPISANA przy 6.A27, nie dopisana obok, i powod jest w niej
    samej.** Poprzednia wersja zadala, zeby w ciele `Compare` staly slowa
    `throw new ArgumentException` — czyli „choc jedna odmowa idzie handlerem".
    Zdanie bylo prawdziwe od 6.A16 i zostawalo prawdziwe, kiedy obok niego siedzialy
    **cztery** odmowy z `Console.Error.WriteLine` + `return 1`, omijajace handler
    i wychodzace BEZ przedrostka `BLAD: `. Bramka meldowala wiec zgode zamiast
    pomiaru — ten sam gatunek usterki, co 6.D30 (dwa martwe pola zgadzaja sie zawsze)
    i 6.B28 (dwa czytniki z jednym bledem).

    Postac liczaca: w ciele `Compare` nie ma ANI JEDNEGO `Console.Error` i ani jednego
    `return 1;`. Jedyne wyjscie z kodem 1 to koncowy werdykt `return failed ? 1 : 0;`,
    ktory nie jest odmowa, a wynikiem porownania.
    """
    kod = _bez_komentarzy(_source())
    body = _cialo_compare(kod)
    assert "compare wymaga dwóch plików" in body, body[:200]
    assert "return 2;" not in body, "compare nadal wraca kodem 2"

    zle = body.count("Console.Error")
    assert zle == 0, (
        f"{zle} odmow w `compare` pisze na stderr wprost i omija wspolny handler, "
        "wiec wychodzi BEZ przedrostka `BŁĄD: ` — ksztalt wyjscia jest wyrocznia "
        "dla czytajacego log CI i dla `grep` (6.A16, 6.A27)")
    assert "return 1;" not in body, (
        "odmowa w `compare` wraca kodem 1 wprost, zamiast rzucic wyjatek — kod byłby "
        "dobry, a ksztalt nie")
    assert "return failed ? 1 : 0;" in body, (
        "koncowy werdykt `compare` zniknal — to jedyne dozwolone wyjscie kodem 1 "
        "z tej metody i nie jest odmowa")


#: Tresci odmow `compare`, ktore 6.A27 przeniosla na wspolny handler. Fragmenty, nie
#: cale napisy z interpolacja — bo `{i}` i `{left.Length}` sa w kodzie, a w wyjsciu
#: nie. Tresci NIE ZMIENIONO, to pole „Poza zakresem" tej pozycji.
ODMOWY_COMPARE = (
    "różna liczba wierszy:",
    "nagłówki telemetrii nie zgadzają się z formatem rdzenia",
    "zła liczba kolumn",
    "różna faza scenariusza",
)


def test_every_compare_refusal_is_thrown_and_none_is_written_to_stderr():
    """Cztery odmowy, wypisane z nazwy — zeby ubytek byl widoczny, a nie cichy.

    **Pole „Poza zakresem" pozycji 6.A27 wylaczalo trzecia odmowe WARUNKOWO**:
    „jezeli pomiar pokaze, ze ona juz przedrostek ma — wtedy pozycja dotyczy dwoch".
    Pomiar pokazal, ze nie ma, i ze jest jeszcze czwarta, o ktorej wpis nie wiedzial
    (`różna faza scenariusza`). Warunek nie zaszedl, wiec pozycja objela cztery.

    Ten test pilnuje kazdej osobno. Sam licznik `Console.Error == 0` przechodzilby
    takze wtedy, gdyby ktos odmowe po prostu USUNAL — a odmowa usunieta jest gorsza
    od odmowy bez przedrostka.
    """
    kod = _bez_komentarzy(_source())
    body = _cialo_compare(kod)
    for tresc in ODMOWY_COMPARE:
        assert tresc in body, (
            "odmowa `compare` zniknela z kodu: " + tresc)
        # Kazda z nich ma stac w wyrazeniu `throw`, a nie w wywolaniu wypisu.
        at = body.index(tresc)
        okolica = body[max(0, at - 200):at]
        assert "throw new ArgumentException" in okolica, (
            "odmowa `" + tresc + "` nie jest rzucana wyjatkiem — kontekst: "
            + okolica[-160:])

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
