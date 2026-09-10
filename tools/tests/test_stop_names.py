#!/usr/bin/env python3
"""Nazwa przystanku porównywana po ZNACZENIU, nie po napisie (6.D111).

Moduł `tools/track/stop_names.py` powstał z pomiaru na 60 przystankach
`data/network/lines.json`. Ten plik pilnuje obu połów: samej reguły — na wejściach
syntetycznych, żeby dało się ją zepsuć bez ruszania `data/` — i warunku, na którym
reguła stoi: że żaden człon kanoniczny nie należy do dwóch różnych stacji.

**Dlaczego warunek jest pilnowany, a nie założony.** `ta_sama` liczy PRZECIĘCIE
zbiorów członów. Gdyby dwie różne stacje dzieliły choć jeden człon, przecięcie
sklejałoby je w jedną i wszystkie kontrole kolejności przestałyby cokolwiek znaczyć —
po cichu, bo sklejenie nie zgłasza się nigdzie. Zmierzone 10.09.2026: **86** członów
kanonicznych na **60** stacji, **zero** kolizji.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
import stop_names as S  # noqa: E402

NETWORK = os.path.join(ROOT, "data", "network", "lines.json")
STOPS = os.path.join(ROOT, "data", "network", "stops.json")

#: Pomiar z 10.09.2026 na `data/network/lines.json`. Liczby są tu **przypięte**,
#: bo pomiar jest treścią pozycji 6.D111 — gdy sieć się zmieni, mają zostać
#: przeliczone ręcznie, a nie dopasowane automatycznie do nowego stanu.
UNIKALNYCH_PRZYSTANKOW = 60
DWUJEZYCZNYCH = 26
CZLONOW_KANONICZNYCH = 86

#: Kolejność języków zmierzona wobec oficjalnego snapshotu GTFS (`stops.json`,
#: pola `name_fr` i `name_nl`), a nie oceniona na oko.
FRANCUSKI_PIERWSZY = 25
NIDERLANDZKI_PIERWSZY = 1


def _przystanki():
    with open(NETWORK, encoding="utf-8") as uchwyt:
        siec = json.load(uchwyt)
    return sorted({stop for line in siec["lines"] for stop in line["stops"]})


def test_pomiar_ksztaltu_nazw_odtwarza_sie():
    """Trzy liczby, z których wyprowadzony jest kształt normalizacji."""
    przystanki = _przystanki()
    assert len(przystanki) == UNIKALNYCH_PRZYSTANKOW, len(przystanki)

    dwuczlonowe = [p for p in przystanki if len(S.czlony(p)) == 2]
    assert len(dwuczlonowe) == DWUJEZYCZNYCH, len(dwuczlonowe)

    # Członów jest DOKŁADNIE jeden albo dwa — trzeci nie wystąpił ani razu.
    liczby = {len(S.czlony(p)) for p in przystanki}
    assert liczby == {1, 2}, f"nazwa o innej liczbie członów: {sorted(liczby)}"

    czlony = {c for p in przystanki for c in S.kanoniczna(p)}
    assert len(czlony) == CZLONOW_KANONICZNYCH, len(czlony)


def test_zaden_czlon_nie_nalezy_do_dwoch_stacji():
    """Warunek, na którym stoi PRZECIĘCIE — pilnowany, a nie założony."""
    gdzie = {}
    for przystanek in _przystanki():
        for czlon in S.kanoniczna(przystanek):
            gdzie.setdefault(czlon, set()).add(przystanek)
    kolizje = {czlon: sorted(gdzie[czlon]) for czlon in gdzie if len(gdzie[czlon]) > 1}
    assert not kolizje, (
        "człon kanoniczny należy do dwóch różnych stacji — `ta_sama` sklei je "
        f"w jedną i żadna kontrola kolejności tego nie zauważy: {kolizje}")


def test_kolejnosc_jezykow_nie_jest_jednolita():
    """Zmierzone wobec GTFS: 25 nazw FR-pierwszy, jedna NL-pierwszy.

    To jest powód, dla którego porównanie nie może być wrażliwe na kolejność —
    i nie jest to hipoteza o tym, co ktoś kiedyś wpisze, tylko stan drzewa.
    """
    if not os.path.isfile(STOPS):
        return
    with open(STOPS, encoding="utf-8") as uchwyt:
        stacje = json.load(uchwyt)["stations"]
    fr = {S.kanoniczny_czlon(s["name_fr"]) for s in stacje if s.get("name_fr")}
    nl = {S.kanoniczny_czlon(s["name_nl"]) for s in stacje if s.get("name_nl")}

    francuski, niderlandzki, nieznane = 0, 0, []
    for przystanek in _przystanki():
        czlony = S.czlony(przystanek)
        if len(czlony) != 2:
            continue
        a, b = (S.kanoniczny_czlon(c) for c in czlony)
        if a in fr and b in nl:
            francuski += 1
        elif a in nl and b in fr:
            niderlandzki += 1
        else:
            nieznane.append(przystanek)

    assert not nieznane, f"GTFS nie rozstrzyga języka członów: {nieznane}"
    assert (francuski, niderlandzki) == (FRANCUSKI_PIERWSZY, NIDERLANDZKI_PIERWSZY), (
        f"kolejność języków ruszyła: {francuski} FR-pierwszy, "
        f"{niderlandzki} NL-pierwszy")


def test_rozjazd_formy_zapisu_nie_jest_rozjazdem_stacji():
    """Cztery formy tej samej nazwy — wejście syntetyczne, `data/` nietknięte.

    Tego żąda pole „Skończone, gdy" pozycji 6.D111 wprost: rozjazd formy zapisu
    ma nie zapalać niczego.
    """
    wzorzec = "Étangs Noirs|Zwarte Vijvers"
    for forma in ("Étangs Noirs|Zwarte Vijvers",
                  "Zwarte Vijvers|Étangs Noirs",       # odwrotna kolejność członów
                  " Étangs Noirs | Zwarte Vijvers ",   # spacje wokół kreski
                  "Etangs Noirs|Zwarte Vijvers",       # bez diakrytyku
                  "Zwarte Vijvers",                    # jeden człon zamiast dwóch
                  "ÉTANGS NOIRS"):                     # sama wielkość liter
        assert S.ta_sama(wzorzec, forma), forma


def test_czlony_zwracaja_SUROWE_nazwy_obciete_i_w_kolejnosci():
    """Druga droga przez ten moduł: człon jako KLUCZ, a nie jako materiał porównania.

    **To dopisała kontrola negatywna KN-3, a nie projekt.** Zdjęcie `.strip()`
    z `czlony` nie zapalało niczego, bo `kanoniczny_czlon` i tak skleja białe znaki —
    na drodze POROWNANIA obcięcie jest zbędne. Nie jest zbędne na drodze drugiej:
    `build_alignment.stop_aliases` i `vertical_profile` budują z tych członów KLUCZE
    czytane przez człowieka i porównywane z polami `name_fr` / `name_nl`, gdzie
    wiodąca spacja jest różnicą.

    Kolejność jest tu sprawdzana z tego samego powodu: `kanoniczna` jest zbiorem
    i kolejności nie niesie, więc gdyby `czlony` ją gubiło, nie zauważyłaby tego
    żadna z pozostałych kontroli.
    """
    assert S.czlony(" Parc | Park ") == ("Parc", "Park"), S.czlony(" Parc | Park ")
    assert S.czlony("Kraainem|Crainhem") == ("Kraainem", "Crainhem"), (
        "kolejność członów zgubiona — a to jedyna droga do oryginalnego zapisu")
    assert S.czlony("Beekkant") == ("Beekkant",), S.czlony("Beekkant")
    assert S.czlony("") == (), S.czlony("")
    assert S.czlony(" | ") == (), (
        "człon złożony z samych białych znaków wszedł do wyniku: %r" % (S.czlony(" | "),))


def test_podmiana_na_inna_stacje_zapala():
    """Druga strona tej samej pary — bez niej reguła „wszystko jest tym samym"."""
    for pierwsza, druga in (("Étangs Noirs|Zwarte Vijvers", "Beekkant"),
                            ("Parc|Park", "Trône|Troon")):
        assert not S.ta_sama(pierwsza, druga), (
            f"dwie różne stacje uznane za tę samą: {pierwsza!r} i {druga!r}")

    # Nazwa pusta nie jest równa niczemu, łącznie z inną pustą: gdyby była,
    # brak nazwy sklejałby ze sobą wszystkie stacje bez nazwy.
    for pierwsza, druga in (("", ""), ("", "Parc|Park"), ("|", "Parc|Park")):
        assert not S.ta_sama(pierwsza, druga), (
            f"nazwa pusta uznana za równą: {pierwsza!r} i {druga!r}")


def test_apostrof_prosty_i_typograficzny_daja_ten_sam_czlon():
    """Zmierzony rozjazd dwóch dawnych normalizacji — dziś obie są jedną.

    `build_alignment.normalise` zostawiała apostrof w napisie, a `_canonical`
    z `test_network_declarations.py` zamieniała go na spację. Obie strony były
    wewnętrznie zgodne, więc nic się nie zapalało; przy pierwszym źródle
    zewnętrznym przestałoby to być prawdą.
    """
    prosty = S.kanoniczny_czlon("Gare de l'Ouest")
    typograficzny = S.kanoniczny_czlon("Gare de l’Ouest")
    assert prosty == typograficzny == "GARE DE L OUEST", (prosty, typograficzny)
    assert S.kanoniczny_czlon("Joséph.-Charlotte") == "JOSEPH CHARLOTTE"


def test_kazde_wejscie_normalizuje_TA_SAMA_regula():
    """„Jedno miejsce" znaczy: te same wejścia dają wszędzie ten sam wynik.

    **To dopisała kontrola negatywna KN-6, a nie projekt.** Cofnięcie
    `build_alignment.normalise` do jej własnej, dawnej reguły — tej, która zostawiała
    apostrof — nie zapalało NICZEGO: obie strony każdego porównania czytają dziś ten
    sam plik, więc rozjazd normalizacji jest niewidoczny dokładnie tak długo, jak
    długo nie ma źródła zewnętrznego. A pozycja 6.D111 istnieje właśnie po to, żeby
    ten rozjazd nie czekał na źródło zewnętrzne w ukryciu.

    Test porównuje więc WYNIKI dwóch wejść z wynikiem reguły wzorcowej, na próbkach
    dobranych tak, żeby dawna różnica była w nich widoczna: apostrof prosty,
    apostrof typograficzny i skrót z kropką.
    """
    import build_alignment  # noqa: E402  (ten sam katalog, wpięty wyżej)
    import test_network_declarations  # noqa: E402

    probki = ("Gare de l'Ouest", "Gare de l\u2019Ouest", "Jos\u00e9ph.-Charlotte",
              "\u00c9tangs Noirs", "Saint-Guidon", "CERIA", "Kraainem")
    for probka in probki:
        wzorzec = S.kanoniczny_czlon(probka)
        assert build_alignment.normalise(probka) == wzorzec, (
            "`build_alignment.normalise` ma własną regułę: "
            f"{build_alignment.normalise(probka)!r} wobec {wzorzec!r}")
        assert test_network_declarations._canonical(probka) == wzorzec, (
            "`test_network_declarations._canonical` ma własną regułę: "
            f"{test_network_declarations._canonical(probka)!r} wobec {wzorzec!r}")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
