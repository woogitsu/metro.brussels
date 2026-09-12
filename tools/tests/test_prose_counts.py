"""Liczby wpisane w PROZĘ obok bramki są porównywane z tym, co bramka mierzy.

**Skąd ta pozycja.** Audyt z 12.09.2026 znalazł dwa zdania nieprawdziwe, oba
stojące bezpośrednio przy przyrządzie, który mierzy dokładnie tę samą rzecz:

* `test_tree_walks.py` opisywał rejestr jako „Trzydzieści osiem: 13 przybitych,
  3 częściowe, 21 WOLNYCH i 1 poza zasięgiem skanu", gdy `len(ZAPADKI)` dawało
  **42** przy rozkładzie 15 / 3 / 23 / 1;
* `test_all.py` mówił „przebieg bez argumentu robi to samo dla 120 modulow",
  gdy modułów było **123**.

**Nie znalazł ich żaden test i nie mógł.** Akapit w `test_tree_walks.py` sam
zapewnia, że „rozjechać się ta lista nie może, bo jest porównywana z drzewem
W OBIE STRONY" — i to prawda o LIŚCIE, a nieprawda o ZDANIU nad nią. Bramka
porównywała słownik z drzewem, więc zdanie o słowniku leżało poza jej zasięgiem:
ten sam kształt, który projekt tropi od 6.D27, tylko o piętro wyżej.

**Dlaczego samo przeliczenie by nie wystarczyło.** Przepisanie „38" na „42"
naprawia dzisiaj i pozwala rozjechać się jutro — a rozjechało się już raz,
niezauważone przez 1 dzień i 4 zapadki. Liczba w prozie potrzebuje tego samego,
co liczba w kodzie: kogoś, kto ją porównuje.

**Cyfry, nie słowa, i obejście jest GŁOŚNE, a nie zakazane.** Dawne zdanie pisało
sumę słownie („Trzydzieści osiem"), a rozbicie cyframi — a zapis słowny to dokładnie
to obejście, które 6.D108 opisało przy `test_report_claims.py`: liczba przestaje być
widoczna dla czytnika, zostając widoczną dla człowieka. Deklaracja zapisana słownie
nie jest jednak przez tę bramkę PRZEPUSZCZANA, tylko NIEWIDZIANA — a dolne ostrze
na czytnik zamienia niewidzenie w czerwone „trafień: 0". Pilnuje tego kontrola
z wejściem syntetycznym, nie skan po słowach: skan zapalałby się na akapitach,
które CYTUJĄ dawne brzmienie, czyli karałby za opisanie przeszłości, a projekt
wymaga tego opisu w każdym przepisanym akapicie.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))

import test_tree_walks as TW

#: Zdanie o rejestrze zapadek. Cztery liczby: razem, przybite, częściowe, wolne.
#: Ostatnia (poza skanem) stoi w tym samym zdaniu i też jest czytana.
WZORZEC_ZAPADEK = re.compile(
    r"(\d+)\s+zapadek:\s*\*\*(\d+)\s+przybitych,\s*(\d+)\s+częściowe,\s*"
    r"(\d+)\s+WOLNE\s+i\s+(\d+)\s+poza\s+zasięgiem\s+skanu\.\*\*")

#: Zdanie o liczbie modułów zestawu.
WZORZEC_MODULOW = re.compile(r"robi to samo dla (\d+) modulow")


def _zrodlo(nazwa):
    with open(os.path.join(ROOT, "tools", "tests", nazwa), encoding="utf-8") as f:
        return f.read()


def _moduly_zestawu():
    """Ile modułów testowych leży pod `tools/tests/` — ta sama populacja,
    o której mówi zdanie w `test_all.py`."""
    katalog = os.path.join(ROOT, "tools", "tests")
    return len([n for n in os.listdir(katalog)
                if n.startswith("test_") and n.endswith(".py")])


def _rozklad_rejestru():
    razem = len(TW.ZAPADKI)
    klasy = {TW.PRZYBITA: 0, TW.CZESCIOWA: 0, TW.WOLNA: 0, TW.POZA_SKANEM: 0}
    for klasa, _modul in TW.ZAPADKI.values():
        klasy[klasa] += 1
    return razem, klasy


def test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem():
    """Cztery liczby z prozy kontra cztery policzone ze słownika."""
    zrodlo = _zrodlo("test_tree_walks.py")
    trafienia = WZORZEC_ZAPADEK.findall(zrodlo)

    # Dolne ostrze na SAM CZYTNIK: przeredagowane zdanie ma paść głośno,
    # a nie przejść przez pustą listę bez ani jednego porównania (6.D27).
    assert len(trafienia) == 1, (
        "zdanie o rejestrze zapadek nie zostało znalezione (trafień: %d) — "
        "albo je przeredagowano, albo wzorzec zgnił; bramka nie ma czego "
        "porównać" % len(trafienia))

    razem, przybite, czesciowe, wolne, poza = (int(x) for x in trafienia[0])
    zm_razem, zm_klasy = _rozklad_rejestru()

    assert razem == zm_razem, (
        "proza mówi o %d zapadkach, a rejestr ma %d" % (razem, zm_razem))
    assert przybite == zm_klasy[TW.PRZYBITA], (
        "proza: %d przybitych, rejestr: %d" % (przybite, zm_klasy[TW.PRZYBITA]))
    assert czesciowe == zm_klasy[TW.CZESCIOWA], (
        "proza: %d częściowe, rejestr: %d" % (czesciowe, zm_klasy[TW.CZESCIOWA]))
    assert wolne == zm_klasy[TW.WOLNA], (
        "proza: %d wolnych, rejestr: %d" % (wolne, zm_klasy[TW.WOLNA]))
    assert poza == zm_klasy[TW.POZA_SKANEM], (
        "proza: %d poza skanem, rejestr: %d" % (poza, zm_klasy[TW.POZA_SKANEM]))

    # Suma klas ma się równać całości — inaczej zdanie może być prawdziwe
    # w każdym członie i nadal gubić zapadkę między klasami.
    assert przybite + czesciowe + wolne + poza == razem, (
        "człony zdania nie sumują się do jego własnej sumy: %d+%d+%d+%d != %d"
        % (przybite, czesciowe, wolne, poza, razem))


def test_zdanie_o_liczbie_modulow_zgadza_sie_z_katalogiem():
    """Liczba modułów z prozy `test_all.py` kontra `tools/tests/`."""
    zrodlo = _zrodlo("test_all.py")
    trafienia = WZORZEC_MODULOW.findall(zrodlo)

    assert len(trafienia) == 1, (
        "zdanie o liczbie modułów nie zostało znalezione (trafień: %d)"
        % len(trafienia))

    zadeklarowane = int(trafienia[0])
    zmierzone = _moduly_zestawu()
    assert zadeklarowane == zmierzone, (
        "proza mówi o %d modułach, a pod `tools/tests/` leży %d"
        % (zadeklarowane, zmierzone))


def test_czytnik_nie_widzi_deklaracji_zapisanej_slownie_i_mowi_o_tym_glosno():
    """Zapis słowny jest obejściem tej bramki — kontrola przyrządu, wejście syntetyczne.

    **Dlaczego nie skan całego pliku.** Pierwsza wersja tego testu szukała słów
    („Trzydzieści", „czterdzieści dwie") w CAŁYM `test_tree_walks.py` i zapaliła
    się natychmiast — na akapicie, który CYTUJE dawne brzmienie, żeby wyjaśnić,
    co się zmieniło. Cytat historyczny wygląda dokładnie jak deklaracja, i jest to
    ta sama obserwacja, którą 6.D108 zrobiło dla raportów: kształtu nie ma.
    Skan po słowach kazałby więc nie opisywać przeszłości, czyli psułby to,
    czego projekt wymaga w każdym przepisanym akapicie.

    **Co zostaje zmierzone zamiast tego.** Że obejście nie jest ciche: deklaracja
    zapisana słownie nie jest przez `WZORZEC_ZAPADEK` widziana wcale, więc
    `test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem` pada na dolnym ostrzu
    („trafień: 0"), a nie przechodzi. Bramka nie da się obejść zapisem słownym —
    da się nią najwyżej zapalić.
    """
    slownie = ("#: Trzydzieści osiem zapadek: **13 przybitych, 3 częściowe,\n"
               "#: 21 WOLNYCH i 1 poza zasięgiem skanu.**")
    assert WZORZEC_ZAPADEK.findall(slownie) == [], (
        "czytnik zobaczył deklarację zapisaną słownie — wtedy zapis słowny "
        "przestaje być głośnym brakiem, a staje się cichym obejściem")

    cyframi = ("#: 42 zapadek: **15 przybitych, 3 częściowe, 23 WOLNE "
               "i 1 poza zasięgiem skanu.**")
    assert WZORZEC_ZAPADEK.findall(cyframi) == [("42", "15", "3", "23", "1")], (
        "czytnik przestał widzieć deklarację zapisaną cyframi — kontrola wyżej "
        "mierzyłaby wtedy nie obejście, tylko własną ślepotę: %s"
        % WZORZEC_ZAPADEK.findall(cyframi))


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
