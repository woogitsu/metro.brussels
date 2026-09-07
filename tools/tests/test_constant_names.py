#!/usr/bin/env python3
"""Ta sama nazwa stalej przy DWOCH roznych wartosciach jest uzasadniona albo jej nie ma.

**Skad ta bramka.** 6.B25. `MIN_RADIUS_M` istnialo w repozytorium dwa razy: 20,0
w `tools/blender/clearance.py` i 90,0 w `tools/tests/test_packages.py`. Ta sama nazwa,
inna wartosc, inne znaczenie, obie zyly obok siebie — a docstring trzeciego pliku
powolywal sie na te martwa jak na obowiazujaca. Nikt tego nie zglosil, bo nie bylo
czym: obie definicje same w sobie sa poprawnym Pythonem.

**Czego ta bramka NIE robi, i to jest w niej najwazniejsze.** Nie zabrania kolizji.
Pomiar z 06.09.2026 pokazal piec nazw o roznych wartosciach w co najmniej dwoch plikach
i **cztery z nich sa poprawne**: `SOURCE_ID`, `DEFAULT_SOURCE_ID` i `SOURCE_CRS` to
tozsamosc modulu — kazdy pobieracz MA miec wlasna, wspolna wartosc byla by bledem —
a `TOLERANCE_M` rozni sie tym, czego dotyczy pomiar. Regula „zadnych powtorzonych nazw"
zapalilaby sie na czterech przypadkach zrobionych dobrze i zostalaby wylaczona po
tygodniu. Dlatego bramka jest **zapadka z uzasadnieniami**: kolizja przechodzi wtedy
i tylko wtedy, gdy stoi nizej z jednozdaniowym powodem, dopisanym w tym samym commicie.

Oba kierunki sa pilnowane. Kolizja bez wpisu zapala bramke. Wpis, ktory przestal
opisywac kolizje, tez ja zapala — inaczej lista gnilaby, a gnijaca lista wyjatkow jest
gorsza od jej braku, bo wyglada na przemyslana.
"""
import ast
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DRZEWA = ("tools", "src")

#: Kolizje uznane po obejrzeniu, nazwa -> powod. Zmierzone 06.09.2026.
#: Dopisanie tu nazwy jest oswiadczeniem, ze kolizja jest zamierzona; test nizej
#: pilnuje, ze wpis bez kolizji znika razem z nia.
UZASADNIONE = {
    "SOURCE_ID":
        "tozsamosc zrodla danych, po jednej na pobieracz — wspolna wartosc scalilaby "
        "OSM, INSPIRE i Brussels Mobility w jeden rejestr proweniencji",
    "DEFAULT_SOURCE_ID":
        "to samo dla domyslnej tozsamosci: `stib_gtfs` i `stib_shapefiles` sa dwoma "
        "roznymi zbiorami STIB, nie dwoma zapisami jednego",
    "SOURCE_CRS":
        "uklad wspolrzednych ZRODLA, a nie docelowy: Lambert 72 (EPSG:31370) dla "
        "danych Regionu, ETRS89-LAEA (EPSG:3035) dla INSPIRE — rowna wartosc "
        "znaczylaby, ze jedno z nich jest reprojektowane nie z tego, czym jest",
    "TOLERANCE_M":
        "tolerancja pomiaru rozni sie tym, co jest mierzone: 0,01 m dla bryly z GLB, "
        "0,001 m dla raportu M7 i dlugosci peronu w potoku",
}


def _stale_modulowe(sciezka):
    """Stale modulowe o wartosci prostej: nazwa -> wartosc.

    Czytane przez `ast`, nie grepem. Grep na `NAZWA = ` zlapalby przypisanie w ciele
    funkcji, w klasie i w napisie — a chodzi wylacznie o to, co modul EKSPORTUJE.
    """
    with open(sciezka, encoding="utf-8") as uchwyt:
        try:
            drzewo = ast.parse(uchwyt.read())
        except SyntaxError:
            return {}
    znalezione = {}
    for wezel in drzewo.body:
        if not isinstance(wezel, ast.Assign) or len(wezel.targets) != 1:
            continue
        cel = wezel.targets[0]
        if not isinstance(cel, ast.Name) or not cel.id.isupper():
            continue
        try:
            wartosc = ast.literal_eval(wezel.value)
        except (ValueError, SyntaxError):
            continue
        if isinstance(wartosc, (int, float, str)) and not isinstance(wartosc, bool):
            znalezione[cel.id] = wartosc
    return znalezione


def kolizje(root=ROOT):
    """Nazwa -> {sciezka: wartosc} dla nazw o WIECEJ NIZ JEDNEJ wartosci."""
    wszystkie = {}
    for drzewo in DRZEWA:
        for katalog, _podkatalogi, pliki in os.walk(os.path.join(root, drzewo)):
            for plik in pliki:
                if not plik.endswith(".py"):
                    continue
                sciezka = os.path.join(katalog, plik)
                wzgledna = os.path.relpath(sciezka, root)
                for nazwa, wartosc in _stale_modulowe(sciezka).items():
                    wszystkie.setdefault(nazwa, {})[wzgledna] = wartosc
    return {n: d for n, d in wszystkie.items() if len(set(d.values())) > 1}


def test_every_clash_of_one_name_over_two_values_is_justified():
    znalezione = kolizje()
    nieuzasadnione = sorted(set(znalezione) - set(UZASADNIONE))
    assert not nieuzasadnione, (
        "nazwa stalej uzyta drugi raz przy INNEJ wartosci, bez wpisu w UZASADNIONE: "
        + "; ".join(
            "%s -> %s" % (n, ", ".join("%s=%r" % (p, w)
                                       for p, w in sorted(znalezione[n].items())))
            for n in nieuzasadnione)
        + ". Albo nazwa jest zla, albo kolizja jest zamierzona i nalezy ja uzasadnic "
          "jednym zdaniem w tym samym commicie")


def test_no_justification_outlives_the_clash_it_describes():
    """Drugi kierunek. Wpis bez kolizji jest gorszy od jego braku: opisuje stan, ktory
    minal, i przy nastepnym czytaniu wyglada na przemyslany."""
    znalezione = kolizje()
    martwe = sorted(set(UZASADNIONE) - set(znalezione))
    assert not martwe, (
        "UZASADNIONE opisuje kolizje, ktorych juz nie ma: " + ", ".join(martwe)
        + " — skresl wpis razem z kolizja, ktora opisywal")


def test_the_name_from_this_task_is_gone():
    """`MIN_RADIUS_M` bylo powodem tej bramki i ma NIE wrocic pod dwiema wartosciami.

    Osobny test, a nie zaufanie do tego wyzej: gdyby ktos dopisal te nazwe do
    `UZASADNIONE`, bramka ogolna zamilklaby, a to jest wlasnie ta kolizja, ktora
    zostala uznana za bledna. Wpisanie jej na liste wyjatkow ma padac tutaj.
    """
    assert "MIN_RADIUS_M" not in UZASADNIONE, (
        "MIN_RADIUS_M zostal wpisany na liste uzasadnionych kolizji — 6.B25 zmierzylo, "
        "ze stala 20,0 w tools/blender/clearance.py byla MARTWA od #50, a prog 90,0 "
        "nalezy czytac z tools/track/validate.py, nie przepisywac")
    assert "MIN_RADIUS_M" not in kolizje(), (
        "MIN_RADIUS_M znowu ma dwie wartosci w repozytorium")


def test_the_package_limits_are_read_from_the_validator_not_copied():
    """Prog pakietu ma pochodzic z `validate.LIMITS`, a nie byc jego kopia.

    Kopia progu rozjezdza sie w JEDNA strone po cichu: os, ktora przestaje spelniac
    prawdziwy prog, przechodzi test, bo tutejszy zostal przy starej wartosci. To jest
    ten sam ksztalt usterki, co martwa stala — tylko trudniejszy do zauwazenia, bo
    liczba jest poprawna w dniu, w ktorym ja przepisano.
    """
    sciezka = os.path.join(ROOT, "tools", "tests", "test_packages.py")
    with open(sciezka, encoding="utf-8") as uchwyt:
        tresc = uchwyt.read()
    assert "VALIDATOR = V.LIMITS" in tresc, (
        "test_packages.py nie czyta granic z walidatora")
    for prog in ("min_radius_m", "min_point_gap_m", "max_point_gap_m"):
        assert 'VALIDATOR["%s"]' % prog in tresc, (
            "prog %s nie jest brany z walidatora" % prog)
    for przepisana in ("MIN_RADIUS_M = ", "MIN_POINT_GAP_M = ", "MAX_POINT_GAP_M = "):
        assert przepisana not in tresc, (
            "granica walidatora wrocila do test_packages.py jako kopia: " + przepisana)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
