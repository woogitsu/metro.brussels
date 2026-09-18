"""Rejestr progow DANYCH — osobny od `ZAPADKI`, bo to inne pojecie.

**Skad ten modul.** 6.D262 znalazlo kontrola przyrzadu dwanascie nazw o ksztalcie
zapadki, ktore sa porownywane w `tools/tests/`, ale docieraja tam przez `modul.NAZWA`,
a `_porownania_zapadek` czyta po stronie stalej wylacznie `ast.Name`. Nie mialy klasy
i nie pilnowalo ich nic. 6.D266 postawilo pytanie: objac je rejestrem `ZAPADKI`,
zalozyc drugi, czy zostawic.

**Decyzja wlasciciela z 18.09.2026: wariant (b) — DRUGI REJESTR, z wlasnymi klasami.**
`ZAPADKA` zostaje przy znaczeniu „prog bramki" i nie przestaje go znaczyc. Te dwanascie
to progi DANYCH: mieszkaja w `tools/track/` i `tools/blender/` i opisuja geometrie toru
albo wiarygodnosc importu, a nie to, czego bramka pilnuje w drzewie.

**Klas decyzja NIE nazwala, i to jest zapisane, a nie przemilczane.** Podzial tematyczny
(geometria / wiarygodnosc / artefakt) bylby ocena estetyczna, a `CLAUDE.md` §8 kaze sie
wtedy zatrzymac i zapytac. Klasy sa wiec wyprowadzone z czegos MIERZALNEGO i czytelnego
z AST: **jaka droga prog dociera do kodu produkcyjnego**. Prog moze docierac kilkoma
naraz, wiec klasa jest ZBIOREM drog, a nie jedna wybrana — wybieranie „wazniejszej"
byloby tym samym gustem tylnymi drzwiami.
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402
import test_tree_walks as TTW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Kod PRODUKCYJNY — wszystko pod `tools/` poza samymi testami. Prog porownywany
#: wylacznie w tescie nie pilnuje danych, tylko wlasnej wartosci.
POZA_PRODUKCJA = os.path.join("tools", "tests")

#: Drogi, ktorymi prog dociera do kodu produkcyjnego. Kazda jest osobnym wezlem AST,
#: wiec nazwanie ich jest odczytem, a nie ocena.
ODRZUCA = "odrzuca"          # porownanie, ktorego galaz podnosi wyjatek
ZGLASZA = "zglasza"          # porownanie zasilajace liste usterek, bez wyjatku
ORZEKA = "orzeka"            # porownanie w wyrazeniu logicznym, bez wlasnej galezi
DOMYSLNY = "domyslny"        # dociera WYLACZNIE jako wartosc domyslna argumentu
ODCIECIE = "odciecie"        # granica wycinka — nie odrzuca, tylko ucina
ARYTMETYKA = "arytmetyka"    # tylko liczenie albo tresc komunikatu


def _podnosi_wyjatek(ciala):
    for zdanie in ciala:
        for pod in ast.walk(zdanie):
            if isinstance(pod, (ast.Raise, ast.Assert)):
                return True
    return False


def _zasila_liste(ciala):
    for zdanie in ciala:
        for pod in ast.walk(zdanie):
            if isinstance(pod, ast.Call) and isinstance(pod.func, ast.Attribute) \
                    and pod.func.attr in ("append", "add", "extend"):
                return True
    return False


def _drogi_w_pliku(zrodlo, nazwy):
    """`{nazwa: {droga}}` dla jednego pliku produkcyjnego."""
    try:
        drzewo = ast.parse(zrodlo)
    except SyntaxError:
        return {}
    rodzic = {}
    for w in ast.walk(drzewo):
        for d in ast.iter_child_nodes(w):
            rodzic[d] = w
    out = {}
    for w in ast.walk(drzewo):
        if not (isinstance(w, ast.Name) and w.id in nazwy):
            continue
        droga = None
        biezacy = w
        # Wspinam sie po rodzicach, bo prog bywa zagniezdzony — `ways[:PROG]` ma
        # miedzy soba `Slice`, a `f"{PROG:.0f}"` ma `FormattedValue`.
        for _ in range(6):
            r = rodzic.get(biezacy)
            if r is None:
                break
            if isinstance(r, ast.Slice):
                droga = ODCIECIE
                break
            if isinstance(r, ast.arguments):
                droga = DOMYSLNY
                break
            if isinstance(r, ast.Compare):
                dziadek = rodzic.get(r)
                while isinstance(dziadek, (ast.BoolOp, ast.UnaryOp)):
                    dziadek = rodzic.get(dziadek)
                if isinstance(dziadek, ast.If):
                    droga = (ODRZUCA if _podnosi_wyjatek(dziadek.body)
                             else ZGLASZA if _zasila_liste(dziadek.body)
                             else ORZEKA)
                elif isinstance(dziadek, ast.Assert):
                    droga = ODRZUCA
                else:
                    droga = ORZEKA
                break
            if isinstance(r, (ast.BinOp, ast.FormattedValue, ast.JoinedStr)):
                droga = ARYTMETYKA
                # arytmetyka jest najslabsza — szukam dalej, moze wyzej stoi porownanie
                biezacy = r
                continue
            biezacy = r
        if droga:
            out.setdefault(w.id, set()).add(droga)
    return out


def drogi_do_produkcji(root, nazwy):
    """`{nazwa: frozenset(drog)}` — jak kazdy prog dociera do kodu produkcyjnego."""
    out = {}
    for baza, _katalogi, pliki in TW.walk(os.path.join(root, "tools"), root):
        rel_kat = os.path.relpath(baza, root)
        if rel_kat.startswith(POZA_PRODUKCJA):
            continue
        for nazwa in sorted(pliki):
            if not nazwa.endswith(".py"):
                continue
            with open(os.path.join(baza, nazwa), encoding="utf-8") as uchwyt:
                znalezione = _drogi_w_pliku(uchwyt.read(), nazwy)
            for prog, drogi in znalezione.items():
                out.setdefault(prog, set()).update(drogi)
    return {k: frozenset(v) for k, v in out.items()}


#: Rejestr progow DANYCH: nazwa -> (zbior drog do produkcji, plik, w ktorym mieszka).
#: Zbior, a nie jedna klasa — bo prog naprawde bywa uzywany kilkoma drogami naraz.
PROGI_DANYCH = {
    "MAX_AXIS_LENGTH_M": (frozenset({ARYTMETYKA}), "tools/track/detail_layout.py"),
    "MAX_ECEF_RESIDUAL_M": (frozenset({DOMYSLNY}), "tools/track/crs.py"),
    "MAX_GAP_M": (frozenset({ZGLASZA}), "tools/blender/tunnel_manifest.py"),
    "MAX_MARKS": (frozenset({ODRZUCA, ARYTMETYKA}), "tools/track/detail_layout.py"),
    "MAX_PLAUSIBLE_VERTICES": (frozenset({ZGLASZA}), "tools/blender/m7_report.py"),
    "MAX_SEED_WAYS": (frozenset({ODCIECIE}), "tools/track/fetch_osm_routes.py"),
    "MAX_TWIST_DEG": (frozenset({ZGLASZA}), "tools/blender/tunnel_manifest.py"),
    "MINIMUM_ARTEFACT_BYTES": (frozenset({DOMYSLNY}), "tools/blender/material_specs.py"),
    "MIN_AXIS_POINTS": (frozenset({ORZEKA}), "tools/blender/tunnel_manifest.py"),
    "MIN_CENTERLINE_POINTS": (frozenset({ORZEKA}), "tools/blender/camera_aim.py"),
    "MIN_PLAUSIBLE_VERTICES": (frozenset({ZGLASZA}), "tools/blender/m7_report.py"),
    "MIN_SENSIBLE_STEP_M": (frozenset({ARYTMETYKA}), "tools/track/detail_layout.py"),
}

#: Wartosci progow, przybite razem z KIERUNKIEM, w ktorym wolno je ruszac.
#: Regula jest ta sama, co dla zapadek bramek, i wynika z tego samego: ruch
#: w strone CIASNIEJSZA zawsze wolno, ruch w strone luzniejsza jest rozluznieniem
#: i ma zapalic bramke. `MAX_` wolno wylacznie OBNIZAC, `MIN_` i `MINIMUM_` —
#: wylacznie PODNOSIC. `MAX_MARKS` jest tu POCHODNA (`MAX_AXIS_LENGTH_M` przez
#: `MIN_SENSIBLE_STEP_M`), wiec rusza sie razem z nimi i to jest zapisane, a nie
#: przemilczane: jego wartosci nie przybijam, przybijam wzor.
WARTOSCI_PROGOW = {
    "MAX_AXIS_LENGTH_M": 40000.0,
    "MAX_ECEF_RESIDUAL_M": 1.0,
    "MAX_GAP_M": 0.001,
    "MAX_PLAUSIBLE_VERTICES": 500000,
    "MAX_SEED_WAYS": 8,
    "MAX_TWIST_DEG": 5.0,
    "MINIMUM_ARTEFACT_BYTES": 1024,
    "MIN_AXIS_POINTS": 2,
    "MIN_CENTERLINE_POINTS": 2,
    "MIN_PLAUSIBLE_VERTICES": 1000,
    "MIN_SENSIBLE_STEP_M": 1.0,
}

#: Prog POCHODNY — liczony z dwoch innych, wiec nie ma wlasnej wartosci do przybicia.
PROG_POCHODNY = "MAX_MARKS"

#: Podloga na populacje skanowana. Skaner oslepiony do zera zgadza sie z pustym
#: rejestrem sam ze soba i przechodzi przybicie celujaco (6.D27).
MIN_PROGOW_ZNALEZIONYCH = 12


def test_rejestr_progow_danych_zgadza_sie_z_drzewem():
    """**Zbior PRZYBITY, porownywany w obie strony — razem z droga, nie samą nazwą.**

    Nazwa bez drogi mowilaby tylko „ten prog istnieje". Droga mowi, czy prog
    czegokolwiek pilnuje — i to jest cala tresc drugiego rejestru.
    """
    zmierzone = drogi_do_produkcji(ROOT, set(PROGI_DANYCH))
    assert len(zmierzone) >= MIN_PROGOW_ZNALEZIONYCH, (
        "skan znalazl %d progow przy podlodze %d — czytnik oslepl, a oslepiony "
        "zgadza sie z pustym rejestrem sam ze soba"
        % (len(zmierzone), MIN_PROGOW_ZNALEZIONYCH))
    oczekiwane = {n: d for n, (d, _p) in PROGI_DANYCH.items()}
    doszly = sorted(set(zmierzone) - set(oczekiwane))
    znikly = sorted(set(oczekiwane) - set(zmierzone))
    assert not doszly, "prog spoza rejestru dociera do produkcji: %s" % doszly
    assert not znikly, (
        "prog z rejestru nie dociera juz do produkcji zadna droga: %s" % znikly)
    inne = sorted((n, sorted(oczekiwane[n]), sorted(zmierzone[n]))
                  for n in oczekiwane if oczekiwane[n] != zmierzone[n])
    assert not inne, (
        "prog dociera do produkcji INNA droga niz zapisana (nazwa, bylo, jest): %s "
        "— droga jest tu trescia: zmiana z `odrzuca` na `zglasza` znaczy, ze prog "
        "przestal odrzucac, a nie ze ktos przestawil literke" % inne)


def test_rejestr_progow_danych_i_lista_niewidzialnych_MOWIA_o_tym_samym():
    """**Dwa zbiory, jedno drzewo — i porownanie w obie strony.**

    `POZA_ZASIEGIEM_KLASYFIKATORA` w `test_tree_walks.py` trzyma te same dwanascie
    nazw od 6.D262. Gdyby zbiory sie rozjechaly, jeden z nich mowilby o drzewie,
    ktorego juz nie ma — a nie widac by tego bylo z zadnego z osobna.
    """
    tamten = set(TTW.POZA_ZASIEGIEM_KLASYFIKATORA)
    ten = set(PROGI_DANYCH)
    assert tamten == ten, (
        "rejestr progow danych i lista niewidzialnych dla klasyfikatora zapadek "
        "rozjechaly sie: tylko tu %s; tylko tam %s"
        % (sorted(ten - tamten), sorted(tamten - ten)))
    wspolne = set(TTW.ZAPADKI) & ten
    assert not wspolne, (
        "nazwa stoi w OBU rejestrach naraz: %s — `ZAPADKA` znaczy `prog bramki`, "
        "a te dwanascie to progi DANYCH, wiec podwojny wpis znaczy, ze jedno "
        "z dwoch pojec przestalo byc soba" % sorted(wspolne))


def test_czytnik_drog_odroznia_POROWNANIE_od_ODCIECIA_i_od_DOMYSLNEJ():
    """**Kontrola przyrzadu: cztery drogi na wejsciu syntetycznym, cztery na wyjsciu.**

    Bez tego sito moze zwracac jedna klase dla wszystkiego i zgadzac sie z rejestrem,
    w ktorym ta klasa stoi — czyli byc zgodne samo ze soba i slepe (6.D276).
    """
    zrodlo = (
        "PROG_A = 5\nPROG_B = 5\nPROG_C = 5\nPROG_D = 5\nPROG_E = 5\n"
        "def f(xs, ile, limit=PROG_B):\n"
        "    if ile > PROG_A:\n"
        "        raise ValueError('za duzo')\n"
        "    out = []\n"
        "    if ile > PROG_C:\n"
        "        out.append('usterka')\n"
        "    return xs[:PROG_D], ile * PROG_E, out\n")
    d = _drogi_w_pliku(zrodlo, {"PROG_A", "PROG_B", "PROG_C", "PROG_D", "PROG_E"})
    assert d.get("PROG_A") == {ODRZUCA}, (
        "porownanie z `raise` w galezi ma dac `odrzuca`: %s" % d.get("PROG_A"))
    assert d.get("PROG_B") == {DOMYSLNY}, (
        "wartosc domyslna argumentu ma dac `domyslny`: %s" % d.get("PROG_B"))
    assert d.get("PROG_C") == {ZGLASZA}, (
        "porownanie zasilajace liste ma dac `zglasza`: %s" % d.get("PROG_C"))
    assert d.get("PROG_D") == {ODCIECIE}, (
        "granica wycinka ma dac `odciecie`, bo nie odrzuca, tylko ucina: %s"
        % d.get("PROG_D"))
    assert d.get("PROG_E") == {ARYTMETYKA}, (
        "samo mnozenie ma dac `arytmetyka`: %s" % d.get("PROG_E"))


def test_ktore_progi_niczego_w_produkcji_NIE_PILNUJA():
    """**Liczba, ktorej pole „Wyjscie" nie zamawialo, a ktora wychodzi z klas.**

    Trzy grupy, kazda z odczytu, nie z podzialu tematycznego:
    prog ODRZUCA sam, prog ORZEKA i decyzje zostawia wolajacemu, albo NIE PILNUJE
    NICZEGO — bo dociera wylacznie jako wartosc domyslna, granica wycinka lub
    skladnik dzialania. Nazwa `MAX_` obiecuje granice; trzecia grupa jej nie
    dotrzymuje i nie mowi o tym nic poza tym testem.

    **Najostrzejszy jest `MAX_SEED_WAYS`:** nie odrzuca nadmiaru, tylko go UCINA
    wycinkiem, wiec dane ponad prog znikaja bez sladu zamiast zostac odrzucone.
    """
    odrzuca = sorted(n for n, (d, _p) in PROGI_DANYCH.items()
                     if d & {ODRZUCA, ZGLASZA})
    orzeka = sorted(n for n, (d, _p) in PROGI_DANYCH.items()
                    if ORZEKA in d and not d & {ODRZUCA, ZGLASZA})
    nic = sorted(n for n, (d, _p) in PROGI_DANYCH.items()
                 if not d & {ODRZUCA, ZGLASZA, ORZEKA})
    assert odrzuca == ["MAX_GAP_M", "MAX_MARKS", "MAX_PLAUSIBLE_VERTICES",
                       "MAX_TWIST_DEG", "MIN_PLAUSIBLE_VERTICES"], odrzuca
    assert orzeka == ["MIN_AXIS_POINTS", "MIN_CENTERLINE_POINTS"], orzeka
    assert nic == ["MAX_AXIS_LENGTH_M", "MAX_ECEF_RESIDUAL_M", "MAX_SEED_WAYS",
                   "MINIMUM_ARTEFACT_BYTES", "MIN_SENSIBLE_STEP_M"], (
        "zbior progow, ktore w produkcji nie pilnuja niczego, rozjechal sie "
        "z pomiarem: %s" % nic)
    assert len(odrzuca) + len(orzeka) + len(nic) == len(PROGI_DANYCH), (
        "trzy grupy nie sumuja sie do rejestru — ktorys prog wpadl w dwie naraz "
        "albo w zadna")


def wartosci_w_drzewie(root):
    """`{nazwa: wartosc}` — odczytane z AST plikow, w ktorych progi mieszkaja."""
    out = {}
    pliki = {plik for _n, (_d, plik) in PROGI_DANYCH.items()}
    for rel in sorted(pliki):
        with open(os.path.join(root, rel), encoding="utf-8") as uchwyt:
            drzewo = ast.parse(uchwyt.read())
        for wezel in drzewo.body:
            if not isinstance(wezel, ast.Assign):
                continue
            for cel in wezel.targets:
                nazwa = getattr(cel, "id", None)
                if nazwa not in WARTOSCI_PROGOW:
                    continue
                try:
                    out[nazwa] = ast.literal_eval(wezel.value)
                except ValueError:
                    pass
    return out


def test_zaden_prog_danych_nie_ruszyl_sie_w_strone_luzniejsza():
    """**To jest ta bramka, ktorej pole „Weryfikacja" 6.D266 zadalo wprost.**

    Do tej pozycji ruszenie ktoregokolwiek z dwunastu progow nie zapalalo NICZEGO:
    stały poza rejestrem `ZAPADKI`, bo docieraja do porownan przez `modul.NAZWA`,
    a klasyfikator czyta po stronie stalej wylacznie `ast.Name`.

    `MAX_` wolno wylacznie OBNIZAC, `MIN_` i `MINIMUM_` — wylacznie PODNOSIC.
    Rownosc, a nie zapadka jednostronna, i to jest wybor: prog DANYCH nie rosnie
    razem z praca tak, jak rosnie populacja pilnowana przez zapadke bramki. Zmiana
    w ktorakolwiek strone jest tu rozstrzygnieciem o geometrii albo o imporcie,
    wiec ma przejsc przez czyjes oko — takze wtedy, gdy zaciska.
    """
    zmierzone = wartosci_w_drzewie(ROOT)
    brak = sorted(set(WARTOSCI_PROGOW) - set(zmierzone))
    assert not brak, (
        "progu nie da sie odczytac z pliku, w ktorym rejestr go umiescil: %s "
        "— albo przeniesiono go gdzie indziej, albo przestal byc literalem" % brak)
    luzniejsze, inne = [], []
    for nazwa, przybita in sorted(WARTOSCI_PROGOW.items()):
        teraz = zmierzone[nazwa]
        if teraz == przybita:
            continue
        gorny = nazwa.startswith("MAX_")
        rozluznil = teraz > przybita if gorny else teraz < przybita
        (luzniejsze if rozluznil else inne).append((nazwa, przybita, teraz))
    assert not luzniejsze, (
        "prog danych ruszyl sie w strone LUZNIEJSZA (nazwa, bylo, jest): %s — "
        "`MAX_` wolno wylacznie obnizac, `MIN_` wylacznie podnosic. Jesli "
        "rozluznienie jest zamierzone, zmien wpis w `WARTOSCI_PROGOW` w tym samym "
        "commicie i napisz, na czym oparta jest nowa granica" % luzniejsze)
    assert not inne, (
        "prog danych zacisniety, a rejestr o tym milczy (nazwa, bylo, jest): %s — "
        "zacisniecie tez jest rozstrzygnieciem o danych i ma zostac zapisane"
        % inne)
    assert PROG_POCHODNY not in WARTOSCI_PROGOW, (
        "prog POCHODNY dostal wlasna przybita wartosc — rusza sie razem ze "
        "skladnikami, wiec przybicie go osobno czerwienieje przy kazdej ich zmianie")


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
