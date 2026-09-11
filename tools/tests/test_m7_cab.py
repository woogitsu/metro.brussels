#!/usr/bin/env python3
"""Kabina kanoniczna: geometria sprawdzana BEZ Blendera.

Ten sam podział, co przy T-212: bryły liczy `tools/blender/m7_cab.py` w czystym
Pythonie, więc każdy wymiar da się sprawdzić bez uruchamiania silnika. Blender
dostaje gotową listę pudełek i robi z nich siatki.

**Najważniejszy test w tym pliku nie pyta o liczby, tylko o ZAWIERANIE:** każdy
wierzchołek każdej bryły musi leżeć wewnątrz przekroju skorupy w tym samym X.
Pudełko wystające przez blachę wygląda na renderze jak kabina, dopóki nie spojrzy się
z zewnątrz — a kabina jest wewnątrz pudła, którego kształt liczy `m7_layout` ze `spec`.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import m7_cab  # noqa: E402
import m7_layout  # noqa: E402

#: Ile brył ma jedna kabina: podłoga, trzy kawałki ściany, dwa pulpitu, dwa fotela.
BRYL_NA_KABINE = 8
#: Ile otworów deklaruje jedna kabina: szyba czołowa i dwa okna boczne.
OTWOROW_NA_KABINE = 3


def _wewnatrz(wielokat, punkt, luz=1e-9):
    """Czy punkt leży w wypukłym wielokącie `(y, z)` — z luzem na zaokrąglenia.

    Przekrój skorupy jest wypukły (prostokąt ze ściętym dachem), więc wystarczy, żeby
    punkt leżał po tej samej stronie każdej krawędzi. Wersja z promieniem nie byłaby
    tu prostsza, a byłaby mniej czytelna.
    """
    y, z = punkt
    n = len(wielokat)
    znaki = []
    for i in range(n):
        y0, z0 = wielokat[i]
        y1, z1 = wielokat[(i + 1) % n]
        znaki.append((y1 - y0) * (z - z0) - (z1 - z0) * (y - y0))
    return all(s >= -luz for s in znaki) or all(s <= luz for s in znaki)


def _rogi(bryla):
    for y in (bryla["y_from_m"], bryla["y_to_m"]):
        for z in (bryla["z_from_m"], bryla["z_to_m"]):
            yield y, z


def test_kazda_bryla_kabiny_miesci_sie_w_skorupie():
    """Sedno: bryła wystająca przez blachę jest usterką, której render z wnętrza nie pokaże."""
    layout = m7_layout.Layout()
    poza = []
    for cab in m7_cab.both_cabs(layout):
        for bryla in cab.solids():
            for x in (bryla["x_from_m"], bryla["x_to_m"]):
                przekroj = layout.section(x)
                for punkt in _rogi(bryla):
                    if not _wewnatrz(przekroj, punkt):
                        poza.append((bryla["name"], x, punkt))
    assert not poza, f"bryła kabiny wystaje poza przekrój pudła: {poza[:5]}"


def test_otwory_kabiny_tez_miesza_sie_w_skorupie():
    """Szyba czołowa i okna boczne to DANE, ale dane o czymś, co ma się zmieścić."""
    layout = m7_layout.Layout()
    poza = []
    for cab in m7_cab.both_cabs(layout):
        for otwor in cab.openings():
            if otwor["kind"] == "windscreen":
                przekroj = layout.section(otwor["at_x_m"])
                rogi = [(otwor["y_from_m"], otwor["z_from_m"]),
                        (otwor["y_to_m"], otwor["z_to_m"])]
            else:
                przekroj = layout.section(otwor["x_from_m"])
                bok = cab.half_width * otwor["side"]
                rogi = [(bok, otwor["z_from_m"]), (bok, otwor["z_to_m"])]
            for punkt in rogi:
                if not _wewnatrz(przekroj, punkt):
                    poza.append((otwor["name"], punkt))
    assert not poza, f"otwór kabiny wypada poza przekrój pudła: {poza[:5]}"


def test_kabina_nie_wychodzi_poza_swoja_dlugosc():
    """Kabina kończy się tam, gdzie `m7_layout` przestaje zabraniać drzwi pasażerskich."""
    layout = m7_layout.Layout()
    dlugosc = m7_layout.DESIGN_CAB_LENGTH_M
    for cab in m7_cab.both_cabs(layout):
        for bryla in cab.solids():
            if cab.end == 0:
                assert 0.0 <= bryla["x_from_m"] and bryla["x_to_m"] <= dlugosc + 1e-9, bryla
            else:
                assert layout.length - dlugosc - 1e-9 <= bryla["x_from_m"], bryla
                assert bryla["x_to_m"] <= layout.length + 1e-9, bryla


def test_fotel_stoi_za_pulpitem_a_nie_w_nim():
    """Kolejność wzdłuż kabiny: szyba, pulpit, fotel, ściana — bez przenikania."""
    cab = m7_cab.Cab(m7_layout.Layout(), end=0)
    bryly = {b["name"]: b for b in cab.solids()}
    pulpit = bryly["cab_front_desk_top"]
    siedzisko = bryly["cab_front_seat_cushion"]
    oparcie = bryly["cab_front_seat_back"]
    sciana = bryly["cab_front_bulkhead_left"]

    assert pulpit["x_to_m"] <= siedzisko["x_from_m"], (pulpit, siedzisko)
    assert siedzisko["x_to_m"] <= oparcie["x_from_m"], (siedzisko, oparcie)
    assert oparcie["x_to_m"] <= sciana["x_from_m"], (
        "oparcie fotela wchodzi w ścianę do przedziału pasażerskiego")

    odstep = siedzisko["x_from_m"] - pulpit["x_to_m"]
    assert abs(odstep - m7_cab.DESIGN_SEAT_GAP_FROM_DESK_M) < 1e-9, odstep


def test_druga_kabina_jest_lustrem_pierwszej():
    """Układ obrotowo symetryczny — ta sama reguła, co przy drzwiach kabinowych."""
    layout = m7_layout.Layout()
    czolo, tyl = m7_cab.both_cabs(layout)
    przod = {b["name"].replace("cab_front_", ""): b for b in czolo.solids()}
    zad = {b["name"].replace("cab_rear_", ""): b for b in tyl.solids()}
    assert set(przod) == set(zad), (sorted(przod), sorted(zad))

    for nazwa, bryla in przod.items():
        lustro = zad[nazwa]
        assert abs((layout.length - bryla["x_to_m"]) - lustro["x_from_m"]) < 1e-4, nazwa
        assert abs((layout.length - bryla["x_from_m"]) - lustro["x_to_m"]) < 1e-4, nazwa
        for pole in ("y_from_m", "y_to_m", "z_from_m", "z_to_m"):
            assert abs(bryla[pole] - lustro[pole]) < 1e-9, (nazwa, pole)


def test_normalne_scian_pudelka_wychodza_na_zewnatrz():
    """Winding sprawdzony ILOCZYNEM WEKTOROWYM, bez Blendera — i to nie jest ozdoba.

    **Pierwsza wersja tej tabeli była ZŁA i pokazał to dopiero render:** klatka
    `_normals` dała `tylna_strona=0.65004`, czyli dwie trzecie widocznej powierzchni
    oglądane od podszewki. Tabela mieszkała wtedy w module z `bpy`, więc jedynym
    sposobem sprawdzenia jej było uruchomienie Blendera — a to znaczy, że usterka
    windingu wychodziła najwcześniej po wygenerowaniu i wyrenderowaniu.

    Test sprawdza znak normalnej każdej z sześciu ścian wobec kierunku, w którym ta
    ściana ma patrzeć. Sześć ścian, sześć różnych kierunków — reguła „wszystkie na
    zewnątrz" spełniona pusto nie jest, bo pudełko ma ściany w obie strony każdej osi.
    """
    pudelko = m7_cab._box("kontrola", "test", 0.0, 2.0, -1.0, 1.0, 0.5, 1.5)
    punkty = m7_cab.verts(pudelko)
    srodek = (1.0, 0.0, 1.0)

    oczekiwane = ((0, 0, -1), (0, 0, 1), (0, -1, 0), (0, 1, 0), (-1, 0, 0), (1, 0, 0))
    assert len(m7_cab.FACES) == len(oczekiwane)
    for sciana, kierunek in zip(m7_cab.FACES, oczekiwane):
        normalna = m7_cab.face_normal([punkty[i] for i in sciana])
        iloczyn = sum(n * k for n, k in zip(normalna, kierunek))
        assert iloczyn > 0, (
            f"ściana {sciana} ma normalną {normalna}, a ma patrzeć w {kierunek}")

        # Druga strona tego samego pytania: normalna ma iść OD środka bryły, a nie
        # do niego. Bez tej asercji tabela odwrócona w komplecie przeszłaby, gdyby
        # ktoś odwrócił razem z nią listę oczekiwanych kierunków.
        rog = punkty[sciana[0]]
        na_zewnatrz = tuple(r - s for r, s in zip(rog, srodek))
        assert sum(n * z for n, z in zip(normalna, na_zewnatrz)) > 0, sciana

    # Każdy wierzchołek należy do dokładnie trzech ścian — pudełko bez dziury i bez
    # ściany policzonej dwa razy.
    from collections import Counter
    ile = Counter(i for sciana in m7_cab.FACES for i in sciana)
    assert set(ile) == set(range(8)), sorted(ile)
    assert set(ile.values()) == {3}, ile


def test_liczba_bryl_i_otworow_jest_przybita():
    """Dolne ostrze na sam generator: pusta lista przeszłaby wszystkie testy wyżej."""
    layout = m7_layout.Layout()
    for cab in m7_cab.both_cabs(layout):
        assert len(cab.solids()) == BRYL_NA_KABINE, [b["name"] for b in cab.solids()]
        assert len(cab.openings()) == OTWOROW_NA_KABINE, cab.openings()

    raport = m7_cab.report(layout)
    assert len(raport["solids"]) == 2 * BRYL_NA_KABINE, len(raport["solids"])
    assert len(raport["openings"]) == 2 * OTWOROW_NA_KABINE, len(raport["openings"])
    nazwy = [b["name"] for b in raport["solids"]]
    assert len(set(nazwy)) == len(nazwy), "dwie bryły o tej samej nazwie"


def test_raport_niesie_zdanie_ze_to_NIE_jest_kabina_M7():
    """Zdanie o tym, czego układ nie odwzorowuje, jedzie razem z geometrią.

    Nie w raporcie obok i nie w docstringu: w pliku, który powstaje przy generowaniu.
    Tak samo zespół dostępu stacji mówi o antresoli, i z tego samego powodu — układ
    kanoniczny obejrzany bez tego zdania wygląda jak rzut czegoś prawdziwego.
    """
    raport = m7_cab.report()
    assert raport["not_modelled"], "raport nie mówi, czego nie odwzorowuje"
    razem = " ".join(raport["not_modelled"]).lower()
    assert "design_assumption" in razem, razem
    assert "stib" in razem, razem


def test_kazdy_wymiar_kabiny_jest_design_assumption():
    """Żadna stała tego modułu nie udaje wymiaru ze `spec`."""
    stale = [n for n in dir(m7_cab)
             if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(stale) >= 20, stale
    brak = [n for n in stale
            if n.replace("DESIGN_", "").lower() not in m7_cab.DESIGN_ASSUMPTIONS]
    assert not brak, f"stała bez wpisu w DESIGN_ASSUMPTIONS: {brak}"
    for nazwa, (wartosc, powod) in m7_cab.DESIGN_ASSUMPTIONS.items():
        assert isinstance(wartosc, (int, float)), (nazwa, wartosc)
        assert len(powod) >= 15, (nazwa, powod)


def test_pudelko_o_niedodatniej_krawedzi_jest_ODMOWA():
    """Kontrola przyrządu: generator, który zwraca puste pudełko, ma się zatrzymać."""
    try:
        m7_cab._box("kontrola", "test", 1.0, 1.0, -1.0, 1.0, 0.0, 1.0)
    except ValueError as blad:
        assert "kontrola" in str(blad), blad
    else:
        raise AssertionError("pudełko o zerowej krawędzi zostało przyjęte")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
