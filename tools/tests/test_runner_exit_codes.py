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


def test_compare_refuses_through_the_common_handler():
    """`compare` bylo jedynym poleceniem sprawdzajacym liczbe argumentow recznie.
    Po 6.A16 rzuca wyjatek — dzieki temu komunikat dostaje ten sam przedrostek
    `BLAD: `, co reszta odmow, wiec ujednolica sie nie tylko liczba, ale i ksztalt."""
    source = _source()
    at = source.index("private static int Compare(")
    body = source[at:source.index("\n    private static", at + 10)]
    assert "compare wymaga dwóch plików" in body, body[:200]
    assert "throw new ArgumentException" in body, (
        "compare nadal odmawia z pominieciem wspolnego handlera")
    assert "return 2;" not in body, "compare nadal wraca kodem 2"

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
