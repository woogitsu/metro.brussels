#!/usr/bin/env python3
"""Profil pionowy: rzędna albo JAWNA niewiadoma, nigdy prosta przez niewiadomą.

Bramki tego modułu są asercjami na LICZBĘ i na BRAK czegoś złego, nie na obecność
czegoś dobrego. Powód jest zmierzony przy pisaniu narzędzia i wart zapisania, bo to
ta sama rodzina usterki, którą projekt nazywa od kilku dni:

Dopasowanie DOKŁADNE po `name_fr` daje **8 z 12** stacji — CSV pisze `De Brouckère`,
`Étangs Noirs`, `Gare de l'Ouest` i `Comte de Flandre`, a oś odpowiednio `De Brouckere`,
`Etangs Noirs`, `Gare De L'Ouest` i `Comte De Flandre`. Wśród czterech zgubionych jest
**De Brouckère, czyli jedna z TRZECH stacji mających głębokość**. Naiwny czytnik
straciłby jedną trzecią znanych danych, wypisał profil i skończył kodem 0.
"""
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import apply_vertical as AV  # noqa: E402
import vertical_profile as VP  # noqa: E402
import stop_names  # noqa: E402

AXIS = os.path.join(ROOT, "data", "track", "L1_A.json")
DEPTHS = os.path.join(ROOT, "data", "network", "station-depths.csv")

#: Ile stacji pakietu A ma dziś rzędną. Zapadka W DÓŁ, nie w górę: wypełnianie
#: `station-depths.csv` należy do człowieka (T-901) i ta liczba ma prawo rosnąć, ale
#: zejście poniżej znaczy, że ktoś skasował dane albo czytnik przestał je widzieć.
#: Zmierzone 07.09.2026 na `e6b4dc1`: De Brouckère -12,0, Parc -20,0, Arts-Loi -12,0.
STACJE_ZE_RZEDNA = 3

#: Wszystkie stacje pakietu A w osi i w CSV. Dopasowanie MUSI objąć wszystkie —
#: asercja na tę liczbę jest jedyną, która łapie cichą utratę stacji na nazwie.
STACJE_PAKIETU_A = 12


def _profil():
    return VP.zbuduj(AXIS, DEPTHS)


def test_dopasowanie_obejmuje_WSZYSTKIE_stacje_a_nie_te_ktore_sie_zgadzaja():
    """8 z 12 to wynik naiwnego dopasowania i wygląda jak sukces. Asercja jest na 12."""
    raport = _profil()
    assert raport["stations_total"] == STACJE_PAKIETU_A, (
        f"dopasowano {raport['stations_total']} stacji, a pakiet A ma {STACJE_PAKIETU_A} "
        "— czytnik gubi stacje na nazwie")


def test_dopasowanie_jednopolowe_gubi_stacje_ZE_RZEDNA():
    """Mierzy, ILE zgubiłby wariant naiwny — i że gubi akurat dane, nie tylko nazwy.

    To jest uzasadnienie zestawu pól. Bez tej liczby `POLA_NAZW_OSI` wygląda na
    ostrożność bez powodu; z nią widać, że wariant jednopolowy traci jedną trzecią
    znanych rzędnych.
    """
    axis = json.load(io.open(AXIS, encoding="utf-8"))
    wiersze = VP.czytaj_glebokosci(DEPTHS, "A")
    po_nazwie_fr = {s.get("name_fr") for s in axis["stations"]}
    dokladne = sum(1 for w in wiersze if w["station_fr"] in po_nazwie_fr)

    assert dokladne < STACJE_PAKIETU_A, (
        "wariant jednopolowy objął wszystkie stacje — jeżeli źródła ujednolicono, "
        "to uzasadnienie zestawu pól straciło powód i trzeba je przepisać")
    zgubione_ze_rzedna = [w["station_fr"] for w in wiersze
                          if w["_depth"] is not None and w["station_fr"] not in po_nazwie_fr]
    assert zgubione_ze_rzedna, (
        "wariant jednopolowy nie gubi ani jednej stacji ZE RZĘDNĄ — jak wyżej")


def test_KAZDE_pole_zestawu_ktore_zarabia_na_miejsce_jest_konieczne():
    """Własność WYPROWADZONA z drzewa, nie liczba wpisana z ręki.

    Zestaw `POLA_NAZW_OSI` ma trzy pola. Zmierzone 07.09.2026 na `e6b4dc1`: zdjęcie
    `name` daje **10 z 12**, a zdjęcie `name_fr` albo `name_nl` — nadal 12 z 12.
    Ta bramka żąda, żeby **co najmniej jedno** pole było konieczne, i nazywa które.
    Bez niej zestaw mógłby urosnąć o pola, które nic nie robią, a nikt by nie zauważył
    — to ta sama rodzina co martwa stała, tylko w zestawie.
    """
    axis = json.load(io.open(AXIS, encoding="utf-8"))
    wiersze = VP.czytaj_glebokosci(DEPTHS, "A")

    def ile_dopasuje(pola_osi):
        uzyte, n = set(), 0
        for w in wiersze:
            szukane = {(w.get(p) or "").strip() for p in VP.POLA_NAZW_CSV}
            szukane = {x for x in szukane if x}
            for idx, s in enumerate(axis["stations"]):
                if idx in uzyte:
                    continue
                klucze = set()
                for pole in pola_osi:
                    if pole == "name":
                        klucze |= set(stop_names.czlony(s.get("name") or ""))
                    elif s.get(pole):
                        klucze.add(s[pole].strip())
                if klucze & szukane:
                    uzyte.add(idx)
                    n += 1
                    break
        return n

    assert ile_dopasuje(VP.POLA_NAZW_OSI) == STACJE_PAKIETU_A, (
        f"pełny zestaw {VP.POLA_NAZW_OSI} dopasowuje {ile_dopasuje(VP.POLA_NAZW_OSI)} "
        f"z {STACJE_PAKIETU_A}")

    konieczne = []
    for zdjete in VP.POLA_NAZW_OSI:
        reszta = tuple(p for p in VP.POLA_NAZW_OSI if p != zdjete)
        if ile_dopasuje(reszta) < STACJE_PAKIETU_A:
            konieczne.append(zdjete)
    assert konieczne, (
        f"żadne pole z {VP.POLA_NAZW_OSI} nie jest konieczne — cały zestaw jest "
        "nadmiarowy i uzasadnienie w docstringu jest nieprawdziwe")
    assert "name" in konieczne, (
        f"konieczne pola to {konieczne}, a docstring modułu twierdzi, że `name` "
        "kosztuje dwie stacje — jedna z tych rzeczy jest nieaktualna")


def test_stacji_ze_rzedna_nie_ubywa():
    raport = _profil()
    assert raport["stations_with_depth"] >= STACJE_ZE_RZEDNA, (
        f"stacji ze rzędną jest {raport['stations_with_depth']} przy zapadce "
        f"{STACJE_ZE_RZEDNA} — dane zniknęły albo czytnik przestał je widzieć")


def test_interpolacja_NIE_PRZECHODZI_przez_stacje_bez_rzednej():
    """Najważniejszy test tego modułu, i przypadek WYSTĘPUJĄCY w dzisiejszych danych.

    Gare Centrale (3731,85 m) leży między De Brouckère (3129,94 m) i Parc (4075,66 m)
    i rzędnej nie ma. Prosta przez nią twierdziłaby, że wiemy, na jakiej głębokości ta
    stacja leży. Asercja jest na BRAK rzędnej w tym zakresie, nie na obecność gdzie indziej.
    """
    raport = _profil()
    stacje = {z["name"]: z for z in raport["stations"]}
    gare = next(z for n, z in stacje.items() if n.startswith("Gare Centrale"))
    assert gare["depth_m"] is None, (
        "Gare Centrale dostała rzędną, a w danych jej nie ma — to znaczy, że "
        "interpolacja przeszła przez niewiadomą")

    brouckere = next(z for n, z in stacje.items() if n.startswith("De Brouckère"))
    parc = next(z for n, z in stacje.items() if n.startswith("Parc"))
    w_zakresie = [p for p in raport["points"]
                  if brouckere["chainage_m"] < p["chainage_m"] < parc["chainage_m"]]
    assert w_zakresie, "zakres De Brouckère..Parc nie ma ani jednego punktu — sprawdź osi"
    z_rzedna = [p for p in w_zakresie if p["depth_m"] is not None]
    assert not z_rzedna, (
        f"{len(z_rzedna)} z {len(w_zakresie)} punktów między De Brouckère i Parc dostało "
        "rzędną, choć między nimi leży stacja bez rzędnej")


def test_kazdy_punkt_niesie_albo_rzedna_albo_JAWNA_niewiadoma():
    """Brak klucza jest gorszy od `null`: czytający nie odróżni go od pominięcia."""
    raport = _profil()
    bez_pola = [p for p in raport["points"]
                if "depth_m" not in p or "confidence" not in p]
    assert not bez_pola, f"{len(bez_pola)} punktów bez pełnej pary pól"
    zle = [p for p in raport["points"]
           if (p["depth_m"] is None) != (p["confidence"] == "unknown")]
    assert not zle, (
        f"{len(zle)} punktów mówi dwie różne rzeczy: rzędna i `confidence` się rozjeżdżają, "
        f"np. {zle[0] if zle else None}")


def test_ekstrapolacji_nie_ma_ani_przed_pierwsza_ani_za_ostatnia_znana():
    raport = _profil()
    znane = [z for z in raport["stations"] if z["depth_m"] is not None]
    pierwsza, ostatnia = znane[0]["chainage_m"], znane[-1]["chainage_m"]
    poza = [p for p in raport["points"]
            if p["depth_m"] is not None
            and not (pierwsza <= p["chainage_m"] <= ostatnia)]
    assert not poza, (
        f"{len(poza)} punktów poza zakresem znanych stacji dostało rzędną — to jest "
        f"ekstrapolacja, np. {poza[0]}")


def test_rzedne_sa_ujemne_bo_kolumna_tego_wymaga():
    raport = _profil()
    dodatnie = [p for p in raport["points"] if p["depth_m"] is not None and p["depth_m"] >= 0]
    assert not dodatnie, f"{len(dodatnie)} punktów ma rzędną >= 0, np. {dodatnie[0] if dodatnie else None}"


def test_interpolacja_jest_monotoniczna_miedzy_dwiema_znanymi():
    """Prosta między dwiema wartościami nie ma prawa mieć ekstremum w środku."""
    raport = _profil()
    ciag = [p for p in raport["points"] if p["depth_m"] is not None]
    assert len(ciag) >= 2, len(ciag)
    rosnie = all(a["depth_m"] <= b["depth_m"] for a, b in zip(ciag, ciag[1:]))
    maleje = all(a["depth_m"] >= b["depth_m"] for a, b in zip(ciag, ciag[1:]))
    assert rosnie or maleje, "ciąg interpolowany nie jest monotoniczny"


def test_ufnosc_interpolacji_nie_jest_wyzsza_od_slabszego_konca():
    raport = _profil()
    kolejnosc = VP.UFNOSCI_Z_RZEDNA
    stacje = {z["name"]: z for z in raport["stations"]}
    for p in raport["points"]:
        if p["depth_m"] is None or not p["between"]:
            continue
        konce = [stacje[n]["confidence"] for n in p["between"]]
        slabszy = max(kolejnosc.index(c) for c in konce)
        assert kolejnosc.index(p["confidence"]) >= slabszy, (
            f"punkt na {p['chainage_m']} m ma ufność {p['confidence']}, a słabszy koniec "
            f"{kolejnosc[slabszy]} — interpolacja podniosła ufność")


def test_pokrycie_podaje_DWIE_liczby_bo_mierza_dwie_rozne_rzeczy():
    """Sama `with_depth_m` czyta się jako „profil pokrywa 7 % osi", a to nieprawda.

    Zmierzone: 468,385 m odcinków łamanej wobec 485,29 m rozpiętości nominalnej.
    Różnica 16,904 m to brak wierzchołka na kilometrażu Parc, nie własność profilu.
    """
    p = _profil()["coverage"]
    for klucz in ("axis_length_m", "with_depth_m", "without_depth_m",
                  "with_depth_percent", "defined_span_m", "defined_span_percent"):
        assert klucz in p, f"brak klucza {klucz} w pokryciu: {sorted(p)}"
    assert p["defined_span_m"] >= p["with_depth_m"], (
        f"rozpiętość nominalna {p['defined_span_m']} < odcinki łamanej {p['with_depth_m']} "
        "— jedna z tych liczb jest policzona źle")
    assert abs(p["with_depth_m"] + p["without_depth_m"] - p["axis_length_m"]) < 0.01, (
        f"{p['with_depth_m']} + {p['without_depth_m']} != {p['axis_length_m']}")


def test_niezgodnosc_depth_i_confidence_jest_ODMOWA():
    """`confidence=unknown` z wypełnionym `depth_m` to dwa zdania, z których jedno kłamie."""
    with tempfile.TemporaryDirectory() as katalog:
        zly = os.path.join(katalog, "zle.csv")
        with io.open(zly, "w", encoding="utf-8") as h:
            h.write("line,package,station_fr,station_nl,depth_m,confidence,note\n")
            h.write("L1/L5,A,Beekkant,Beekkant,-9.0,unknown,\n")
        try:
            VP.czytaj_glebokosci(zly, "A")
        except ValueError as blad:
            assert "unknown" in str(blad) and "-9.0" in str(blad), str(blad)
        else:
            raise AssertionError("czytnik przyjął confidence=unknown z wypełnionym depth_m")


def test_dodatnia_glebokosc_jest_ODMOWA():
    with tempfile.TemporaryDirectory() as katalog:
        zly = os.path.join(katalog, "zle.csv")
        with io.open(zly, "w", encoding="utf-8") as h:
            h.write("line,package,station_fr,station_nl,depth_m,confidence,note\n")
            h.write("L1/L5,A,Beekkant,Beekkant,12.0,estimated,\n")
        try:
            VP.czytaj_glebokosci(zly, "A")
        except ValueError as blad:
            assert "UJEMNEJ" in str(blad), str(blad)
        else:
            raise AssertionError("czytnik przyjął dodatnią głębokość")


def test_nierozpoznana_ufnosc_jest_ODMOWA_a_nie_cichym_pominieciem():
    with tempfile.TemporaryDirectory() as katalog:
        zly = os.path.join(katalog, "zle.csv")
        with io.open(zly, "w", encoding="utf-8") as h:
            h.write("line,package,station_fr,station_nl,depth_m,confidence,note\n")
            h.write("L1/L5,A,Beekkant,Beekkant,-9.0,mniej_wiecej,\n")
        try:
            VP.czytaj_glebokosci(zly, "A")
        except ValueError as blad:
            assert "mniej_wiecej" in str(blad), str(blad)
        else:
            raise AssertionError("czytnik przyjął nierozpoznaną wartość confidence")


def test_stacja_bez_pary_jest_ODMOWA_z_KODEM_a_nie_krotszym_profilem():
    """Odmowa musi mieć własny kod wyjścia — inaczej wołający nie odróżni jej od zera."""
    with tempfile.TemporaryDirectory() as katalog:
        wyjscie = os.path.join(katalog, "profil.json")
        zly = os.path.join(katalog, "zle.csv")
        with io.open(zly, "w", encoding="utf-8") as h:
            h.write("line,package,station_fr,station_nl,depth_m,confidence,note\n")
            h.write("L1/L5,A,Stacja Ktorej Nie Ma,Onbestaand,-9.0,estimated,\n")
        done = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "track", "vertical_profile.py"),
             "--axis", AXIS, "--depths", zly, "--out", wyjscie],
            capture_output=True, text=True)
        assert done.returncode == VP.KOD_BRAK_DOPASOWANIA, (done.returncode, done.stderr[-300:])
        assert "Stacja Ktorej Nie Ma" in done.stderr, done.stderr[-300:]
        assert not os.path.exists(wyjscie), "odmowa zapisała plik wyjściowy"


def test_narzedzie_konczy_kodem_zero_i_pisze_plik_na_prawdziwych_danych():
    with tempfile.TemporaryDirectory() as katalog:
        wyjscie = os.path.join(katalog, "profil.json")
        done = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "track", "vertical_profile.py"),
             "--axis", AXIS, "--depths", DEPTHS, "--out", wyjscie],
            capture_output=True, text=True)
        assert done.returncode == 0, (done.returncode, done.stderr[-400:])
        raport = json.load(io.open(wyjscie, encoding="utf-8"))
        assert raport["stations_total"] == STACJE_PAKIETU_A
        assert len(raport["points"]) == len(
            json.load(io.open(AXIS, encoding="utf-8"))["points"]), (
            "profil ma inną liczbę punktów niż oś")
        assert "NIEWIADOMA" in done.stdout, "wypis nie nazywa ani jednej niewiadomej"


def test_narzedzie_nie_pisze_do_data():
    """`data/` jest tylko do odczytu (`CLAUDE.md` §4.6) — sprawdzane odciskiem, nie ufnością."""
    import hashlib
    przed = hashlib.sha256(io.open(DEPTHS, "rb").read()).hexdigest()
    _profil()
    po = hashlib.sha256(io.open(DEPTHS, "rb").read()).hexdigest()
    assert przed == po, "narzędzie zmieniło plik w data/"


# Straznik `__main__`: bez niego `python3 tools/tests/test_vertical_profile.py` konczy
# sie kodem 0, nie wykonawszy ani jednego testu — czyli daje zielone zero. Pilnuje tego
# `test_every_test_module_can_be_run_directly` i ta bramka zapalila sie na tym module.
# --- 6.D120: wynik profilu wchodzi do osi ----------------------------------------

#: Ile granic wiedzy ma oś A po nałożeniu profilu: wejście w odcinek znany i wyjście
#: z niego. Zmierzone 11.09.2026 — to NIE jest próg, tylko liczba mierząca dane.
GRANIC_NA_OSI_A = 2


def _os_z_profilem():
    axis = json.load(io.open(os.path.join(ROOT, "data", "track", "L1_A.json"),
                             encoding="utf-8"))
    profil = VP.zbuduj(os.path.join(ROOT, "data", "track", "L1_A.json"),
                       os.path.join(ROOT, "data", "network", "station-depths.csv"))
    return axis, profil, AV.zastosuj(axis, profil)


def test_rzedne_wchodza_do_osi_tam_gdzie_sa_i_nigdzie_indziej():
    """Sedno 6.D120: Z z rejestru na odcinku znanym, zero poza nim — punkt po punkcie.

    Porównanie idzie z PROFILEM, a nie z listą kilometraży wpisaną do testu: druga
    lista rozjechałaby się z pierwszą przy pierwszej zmianie rejestru głębokości,
    a test dalej świeciłby na zielono.
    """
    _axis, profil, wynik = _os_z_profilem()
    assert len(wynik["points"]) == len(profil["points"])

    ze_rzedna = 0
    for punkt, wpis in zip(wynik["points"], profil["points"]):
        z = punkt[2]
        if wpis["depth_m"] is None:
            assert z == 0.0, (wpis["chainage_m"], z)
        else:
            assert abs(z - wpis["depth_m"]) < 1e-9, (wpis["chainage_m"], z, wpis["depth_m"])
            assert z < 0.0, "rzędna główki szyny pod ulicą ma być ujemna"
            ze_rzedna += 1

    assert ze_rzedna == wynik["vertical"]["points_with_z"], ze_rzedna
    assert 0 < ze_rzedna < len(wynik["points"]), (
        "albo cała oś dostała rzędne, albo żaden punkt — w obu przypadkach ten test "
        "nie mierzy tego, co mówi")


def test_granica_wiedzy_jest_USKOKIEM_i_jest_policzona():
    """Nie wygładzona — i policzalna, bo tego żąda pole „Skończone, gdy".

    Uskok jest artefaktem granicy wiedzy, nie spadkiem toru. Wygładzenie go
    twierdziłoby, że znamy spadek prowadzący do znanego odcinka — czyli dokładnie to,
    czego zabrania reguła interpolacji z `vertical_profile.py`.
    """
    _axis, _profil, wynik = _os_z_profilem()
    granice = wynik["vertical"]["boundaries"]
    assert len(granice) == GRANIC_NA_OSI_A, granice

    wejscie = [g for g in granice if g["into"] == "known"]
    wyjscie = [g for g in granice if g["into"] == "unknown"]
    assert len(wejscie) == 1 and len(wyjscie) == 1, granice

    for granica in granice:
        assert abs(granica["step_m"]) > 1.0, (
            "uskok mniejszy niż metr — granica została wygładzona: %s" % granica)
        assert 0.0 in (granica["z_before_m"], granica["z_after_m"]), (
            "po jednej stronie granicy ma stać zero, czyli BRAK rzędnej: %s" % granica)
        assert granica["chainage_m"] > 0.0, granica

    # Uskok wejściowy równa się pierwszej znanej rzędnej — bo druga strona to zero.
    assert abs(wejscie[0]["step_m"] - wejscie[0]["z_after_m"]) < 1e-9, wejscie


def test_os_wynikowa_mowi_czym_jest_jej_zero():
    """Z = 0 znaczy BRAK rzędnej, nie główkę szyny na poziomie ulicy.

    Zdanie o tym jedzie w wyniku, a nie tylko w dokumentacji — oś wynikowa bywa
    czytana bez tego repozytorium (przez `tunnel_sweep.py`, przez Godota, przez
    kogokolwiek), a płaski odcinek wygląda wtedy jak rzędna równa zeru.
    """
    _axis, _profil, wynik = _os_z_profilem()
    pionowy = wynik["vertical"]
    assert pionowy["status"] == AV.STATUS_CZASTKOWY
    assert pionowy["status"] not in ("modelled", "not_modelled"), (
        "status cząstkowy nie może udawać żadnego z dwóch dawnych")
    nota = pionowy["note"].lower()
    assert "brak" in nota, pionowy["note"]
    assert "poziom" in nota and "ulic" in nota, pionowy["note"]
    assert pionowy["coverage"]["defined_span_percent"] < 100.0, pionowy["coverage"]
    assert pionowy["source_profile"]["depths_sha256"], (
        "wynik nie niesie odcisku rejestru, z którego wzięły się rzędne")


def test_profil_z_innej_osi_jest_ODMOWA():
    """Cicha korekta byłaby tu gorsza niż brak narzędzia."""
    axis, profil, _wynik = _os_z_profilem()

    obcy = dict(profil, axis_id="L9_Z")
    try:
        AV.zastosuj(axis, obcy)
    except ValueError as blad:
        assert "L9_Z" in str(blad), blad
    else:
        raise AssertionError("profil z innej osi został przyjęty")

    krotki = dict(profil, points=profil["points"][:-1])
    try:
        AV.zastosuj(axis, krotki)
    except ValueError as blad:
        assert "punkt" in str(blad), blad
    else:
        raise AssertionError("profil o innej liczbie punktów został przyjęty")


def test_narzedzie_odmawia_zapisu_do_data():
    """`data/` jest tylko do odczytu (§4.6) i narzędzie ma to wiedzieć samo."""
    kod = AV.main(["--axis", os.path.join(ROOT, "data", "track", "L1_A.json"),
                   "--profile", os.path.join(ROOT, "data", "track", "L1_A.json"),
                   "--out", os.path.join(ROOT, "data", "track", "nie-wolno.json")])
    assert kod == AV.KOD_ROZJAZD, kod
    assert not os.path.exists(os.path.join(ROOT, "data", "track", "nie-wolno.json"))


def test_przebieg_z_wiersza_polecen_wypisuje_kazda_granice():
    """Wypis jest tym, co człowiek zobaczy — granica ma być w nim, nie tylko w JSON-ie."""
    with tempfile.TemporaryDirectory() as tmp:
        profil_path = os.path.join(tmp, "profil.json")
        wynik_path = os.path.join(tmp, "os.json")
        gotowe = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "track", "vertical_profile.py"),
             "--axis", os.path.join(ROOT, "data", "track", "L1_A.json"),
             "--depths", os.path.join(ROOT, "data", "network", "station-depths.csv"),
             "--out", profil_path],
            capture_output=True, text=True, timeout=120)
        assert gotowe.returncode == 0, gotowe.stdout + gotowe.stderr

        gotowe = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "track", "apply_vertical.py"),
             "--axis", os.path.join(ROOT, "data", "track", "L1_A.json"),
             "--profile", profil_path, "--out", wynik_path],
            capture_output=True, text=True, timeout=120)
        assert gotowe.returncode == 0, gotowe.stdout + gotowe.stderr

    wiersze = [w for w in gotowe.stdout.splitlines() if "granica wiedzy" in w]
    assert len(wiersze) == GRANIC_NA_OSI_A, gotowe.stdout
    assert "uskok" in gotowe.stdout, gotowe.stdout
    assert "nie spadkiem toru" in gotowe.stdout, gotowe.stdout


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
