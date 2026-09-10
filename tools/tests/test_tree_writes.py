#!/usr/bin/env python3
"""Żaden test nie pisze do pliku ŚLEDZONEGO w drzewie głównym.

**Skąd ta bramka.** Pozycja 6.D90 weszła do kolejki z tezą, że narzędzie mutacyjne
zmienia pliki w `data/` w miejscu. Pomiar 10.09.2026 tezę **obalił** — `targets()`
chodzi wyłącznie po `tools/` i bierze wyłącznie `.py`, a `check_one` pisze do kopii
z `git worktree add --detach`, stojącej w katalogu tymczasowym — ale przy okazji
znalazł to samo zjawisko gdzie indziej i naprawdę.

Sonda `git status --porcelain` odpytywana **co 50 ms** przez cały przebieg zestawu
(2158 testów) złapała `M tools/blender/lod_paths.py` w **11 próbkach**: trzy kontrole
z `test_mutation_sweep.py` zmieniały ten plik W DRZEWIE GŁÓWNYM i przywracały go
w `finally`. Przywrócenie działa, więc po przebiegu nie widać nic — ale równoległa
kontrola czystości w tym oknie widzi naruszenie reguły 6, którego nikt nie popełnił.
Dokładnie to opisuje pole „Skąd" pozycji 6.D90, tylko o innym pliku.

**Dlaczego bramka statyczna, a nie sonda.** Sonda mierzy tylko to, w co trafi między
próbkami. Skan drzewa składni znalazł **siedem** miejsc zapisu w **trzech** modułach,
a sonda przez cały przebieg pokazała **jeden** plik: pozostałe okna są krótsze niż
50 ms. Przyrząd oparty na próbkowaniu meldowałby więc czystość, której nie sprawdził
— i to jest ta sama rodzina usterki, którą projekt tropi od 6.D27.

**Czego ta bramka NIE łapie, wypisane wprost:** zapisu przez `shutil`, `os.replace`,
`pathlib.Path.write_text` ani przez podproces. Łapie `open(..., "w"/"a")` ze ścieżką
zbudowaną z `ROOT` — kształt, który w tym repozytorium wystąpił siedem razy na siedem.
Rozszerzanie o kolejne kształty ma iść za pomiarem, nie za wyobraźnią.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tree_walk as TW  # noqa: E402

ROOT = TW.ROOT
TESTY = os.path.join(ROOT, "tools", "tests")

#: Nazwa katalogu głównego repozytorium w kodzie testów. Szukana jako CAŁE SŁOWO,
#: żeby `SUBROOT` albo `ROOTS` nie wchodziły do wyniku przez przypadek.
SLOWO_ROOT = re.compile(r"\bROOT\b")

#: Tryby `open`, przy których plik może zostać zmieniony.
ZNAKI_ZAPISU = "wax+"

#: JAWNA, ZAMKNIĘTA lista miejsc, które piszą do pliku śledzonego i **jeszcze nie
#: zostały przeniesione na kopię**. Każda pozycja to `(moduł, ile miejsc, powód)`.
#: Nie jest to lista wyjątków „bo tak trzeba" — to lista DŁUGU, i dlatego zapadka
#: niżej pozwala jej wyłącznie maleć.
#:
#: Obie pozycje weszły do drzewa w tej samej sesji co ta bramka (6.D79 i 6.D89)
#: i obie mają ten sam kształt co naprawione: zapis, pomiar, przywrócenie w `finally`.
#: Nie są naprawiane tutaj, bo `CLAUDE.md` §4.10 mówi „jedno zadanie = jedna gałąź"
#: i żaden z tych plików nie należy do pozycji 6.D90 — są zapisane jako zauważone
#: w jej raporcie i mają wrócić własną pozycją.
DLUG = {
    "test_dotnet_version.py": (
        3, "kontrola parsera pinu podmienia `global.json` w drzewie (6.D79)"),
    "test_provenance_classes.py": (
        2, "kontrola zbioru klas podmienia `docs/02-simulation.md` w drzewie (6.D89)"),
}

#: Zapadka: tyle miejsc zapisu wolno mieć całemu katalogowi testów. Zmierzone
#: 10.09.2026 **po** przeniesieniu pięciu miejsc z `test_mutation_sweep.py` na kopię:
#: przedtem **7**, dziś **5**. Wolno ją wyłącznie OBNIŻAĆ — podniesienie znaczyłoby,
#: że ktoś dopisał kolejne miejsce, a to jest dokładnie to, czemu bramka ma zapobiec.
MAX_ZAPISOW_W_DRZEWIE = 5


def _moduly():
    for name in sorted(os.listdir(TESTY)):
        if name.endswith(".py"):
            yield name, os.path.join(TESTY, name)


def _tryb_zapisu(node):
    """Tryb `open`, jeśli pozwala zmienić plik; inaczej `None`."""
    tryb = None
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        if isinstance(node.args[1].value, str):
            tryb = node.args[1].value
    for slowo in node.keywords:
        if slowo.arg == "mode" and isinstance(slowo.value, ast.Constant):
            if isinstance(slowo.value.value, str):
                tryb = slowo.value.value
    if tryb and any(znak in tryb for znak in ZNAKI_ZAPISU):
        return tryb
    return None


def _nazwy_od_roota(wezly):
    """Nazwy przypisane z wyrażenia, w którym pada `ROOT`.

    Wyrażenie czytane jest przez `ast.unparse`, a nie `ast.get_source_segment`:
    ten drugi dzieli źródło na wiersze przy KAŻDYM wywołaniu, a wywołań jest jedno
    na przypisanie w całym katalogu testów — pierwsza wersja tej bramki nie skończyła
    się w 110 s. `unparse` daje napis znormalizowany, w którym `ROOT` stoi tak samo.

    Propagacja jest płytka i to jest wybór: `pelna = os.path.join(ROOT, plik)`
    a potem `open(pelna, "w")` to DOKŁADNIE ten kształt, który 6.D90 znalazło
    w drzewie, a głębsza analiza przepływu kupiłaby tu wyłącznie fałszywe alarmy.
    """
    nazwy = set()
    for korzen in wezly:
        for wezel in ast.walk(korzen):
            if isinstance(wezel, ast.Assign):
                odcinek = ast.unparse(wezel.value)
                if SLOWO_ROOT.search(odcinek):
                    for cel in wezel.targets:
                        if isinstance(cel, ast.Name):
                            nazwy.add(cel.id)
    return nazwy


def _otwarcia_do_zapisu(funkcja):
    """`[(węzeł Call, tryb)]` — wywołania `open` w trybie zmieniającym plik."""
    out = []
    for wezel in ast.walk(funkcja):
        if not (isinstance(wezel, ast.Call) and isinstance(wezel.func, ast.Name)
                and wezel.func.id == "open" and wezel.args):
            continue
        tryb = _tryb_zapisu(wezel)
        if tryb is not None:
            out.append((wezel, tryb))
    return out


def _parametry(funkcja):
    a = funkcja.args
    return [arg.arg for arg in (a.posonlyargs + a.args)]


def _pisze_przez_parametr(funkcja):
    """Numery parametrów, które ta funkcja otwiera do ZAPISU.

    **Ten kształt dopisała kontrola negatywna, nie projekt bramki.** Pierwsza wersja
    skanu patrzyła wyłącznie na wyrażenie w samym `open`, i przy przywróceniu
    kontroli 6.B38 do zapisu w drzewie głównym **wyszła zielona**: zapis siedzi
    w pomocniku `_z_dopiskiem(cel, dopisek)`, gdzie `cel` jest PARAMETREM, a nazwa
    `ROOT` nie pada ani razu — pada u wołającego. Bramka omijała więc dokładnie tę
    postać, dla której powstała, i wypisanie tego tutaj jest częścią pomiaru.
    """
    numery = []
    parametry = _parametry(funkcja)
    for wezel, _tryb in _otwarcia_do_zapisu(funkcja):
        cel = wezel.args[0]
        if isinstance(cel, ast.Name) and cel.id in parametry:
            numery.append(parametry.index(cel.id))
    return numery


def miejsca_zapisu(zrodlo):
    """`[(wiersz, funkcja, wyrażenie ścieżki, tryb)]` dla jednego modułu.

    Dwa kształty, oba zmierzone na tym repozytorium:

    1. `open(<wyrażenie z ROOT>, "w")` — wprost albo przez zmienną lokalną;
    2. `pomocnik(<wyrażenie z ROOT>)`, gdzie `pomocnik` otwiera swój parametr
       do zapisu. Wynik jest przypisany do WOŁANIA, bo to wołający wybiera drzewo.
    """
    drzewo = ast.parse(zrodlo)
    globalne = _nazwy_od_roota(
        [w for w in drzewo.body if isinstance(w, ast.Assign)])
    funkcje = [w for w in ast.walk(drzewo)
               if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef))]
    piszace = {f.name: _pisze_przez_parametr(f) for f in funkcje}
    piszace = {nazwa: numery for nazwa, numery in piszace.items() if numery}

    znalezione = []
    for funkcja in funkcje:
        lokalne = _nazwy_od_roota([funkcja]) | globalne

        def _od_roota(wezel):
            odcinek = ast.unparse(wezel)
            if SLOWO_ROOT.search(odcinek):
                return odcinek
            if isinstance(wezel, ast.Name) and wezel.id in lokalne:
                return odcinek
            return None

        for wezel, tryb in _otwarcia_do_zapisu(funkcja):
            odcinek = _od_roota(wezel.args[0])
            if odcinek is not None:
                znalezione.append((wezel.lineno, funkcja.name, odcinek, tryb))

        for wezel in ast.walk(funkcja):
            if not (isinstance(wezel, ast.Call) and isinstance(wezel.func, ast.Name)):
                continue
            numery = piszace.get(wezel.func.id)
            if not numery:
                continue
            for numer in numery:
                if numer < len(wezel.args):
                    odcinek = _od_roota(wezel.args[numer])
                    if odcinek is not None:
                        znalezione.append(
                            (wezel.lineno, funkcja.name,
                             f"{wezel.func.id}({odcinek}, ...)", "przez pomocnika"))
    return sorted(set(znalezione))


def wszystkie_miejsca():
    """`{moduł: [miejsca]}` dla całego katalogu testów, bez modułów pustych."""
    out = {}
    for nazwa, sciezka in _moduly():
        with open(sciezka, encoding="utf-8") as uchwyt:
            miejsca = miejsca_zapisu(uchwyt.read())
        if miejsca:
            out[nazwa] = miejsca
    return out


def test_zadna_kontrola_nie_pisze_do_pliku_sledzonego_poza_lista_dlugu():
    """Nowe miejsce zapisu do drzewa głównego zapala bramkę, stare są wymienione."""
    znalezione = wszystkie_miejsca()
    nadmiar = {}
    for modul, miejsca in znalezione.items():
        wolno = DLUG.get(modul, (0, ""))[0]
        if len(miejsca) > wolno:
            nadmiar[modul] = [(w, f, s) for w, f, s, _t in miejsca][wolno:]
    assert not nadmiar, (
        "kontrola pisze do pliku zbudowanego ze ścieżki repozytorium — w oknie zapisu "
        "równoległa kontrola czystości widzi naruszenie reguły 6, którego nikt nie "
        f"popełnił; przenieś zapis na kopię (wzór: `_cele_na_boku`): {nadmiar}")


def test_lista_dlugu_nie_gnije():
    """Moduł spłacony wypada z listy — inaczej lista rośnie i przestaje coś znaczyć."""
    znalezione = wszystkie_miejsca()
    for modul, (ile, powod) in sorted(DLUG.items()):
        assert modul in znalezione, (
            f"{modul} nie ma już ani jednego miejsca zapisu — zdejmij go z DLUG "
            f"({powod})")
        assert len(znalezione[modul]) == ile, (
            f"{modul}: miejsc jest {len(znalezione[modul])}, a lista mówi {ile} — "
            "zaktualizuj liczbę albo, jeśli spadła do zera, zdejmij wpis")


def test_zapadka_stoi_na_zmierzonej_liczbie():
    """Zapadka wolno tylko maleć, i musi zgadzać się z drzewem co do jedności."""
    ile = sum(len(m) for m in wszystkie_miejsca().values())
    assert ile <= MAX_ZAPISOW_W_DRZEWIE, (
        f"miejsc zapisu jest {ile} przy zapadce {MAX_ZAPISOW_W_DRZEWIE} — "
        "nowe miejsce zapisu do drzewa nie wchodzi razem z podniesieniem zapadki")
    assert ile == MAX_ZAPISOW_W_DRZEWIE, (
        f"miejsc zapisu jest {ile}, a zapadka stoi na {MAX_ZAPISOW_W_DRZEWIE} — "
        f"obniż ją do {ile} w tym samym commicie, w którym spłacasz dług")


def test_skan_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola PRZYRZĄDU: skan bez trafień jest nieodróżnialny od skanu ślepego.

    Trzy wejścia syntetyczne, każde nazwane osobno, bo każde może zgasnąć inaczej:
    zapis wprost z `ROOT`, zapis przez zmienną pośrednią (kształt, który 6.D90
    znalazło w drzewie) i zapis do katalogu tymczasowego, który zapalić się NIE MA.
    """
    wprost = miejsca_zapisu(
        'import os\nROOT = "/x"\n'
        'def test_a():\n    open(os.path.join(ROOT, "a.py"), "w").write("")\n')
    assert len(wprost) == 1, wprost

    przez_zmienna = miejsca_zapisu(
        'import os\nROOT = "/x"\n'
        'def test_b():\n'
        '    pelna = os.path.join(ROOT, "a.py")\n'
        '    with open(pelna, "w") as u:\n        u.write("")\n')
    assert len(przez_zmienna) == 1, przez_zmienna

    tymczasowy = miejsca_zapisu(
        'import os, tempfile\nROOT = "/x"\n'
        'def test_c():\n'
        '    with tempfile.TemporaryDirectory() as t:\n'
        '        with open(os.path.join(t, "a.py"), "w") as u:\n            u.write("")\n')
    assert tymczasowy == [], (
        "skan zgłasza zapis do katalogu tymczasowego — to fałszywy alarm, "
        f"a nie surowość: {tymczasowy}")

    odczyt = miejsca_zapisu(
        'import os\nROOT = "/x"\n'
        'def test_d():\n    open(os.path.join(ROOT, "a.py"), encoding="utf-8").read()\n')
    assert odczyt == [], f"skan bierze ODCZYT za zapis: {odczyt}"

    # Czwarty kształt, dopisany PO tym, jak kontrola negatywna KN-3 wyszła zielona:
    # zapis siedzi w pomocniku, a drzewo wybiera wołający.
    przez_pomocnika = miejsca_zapisu(
        'import os\nROOT = "/x"\n'
        'def _pomocnik(cel, tekst):\n'
        '    with open(cel, "a") as u:\n        u.write(tekst)\n'
        'def test_e():\n    _pomocnik(os.path.join(ROOT, "a.py"), "x")\n')
    assert len(przez_pomocnika) == 1, (
        "skan nie widzi zapisu przez pomocnika — dokładnie ta postać przeszła "
        f"pierwszą wersję tej bramki: {przez_pomocnika}")

    pomocnik_do_tymczasowego = miejsca_zapisu(
        'import os, tempfile\nROOT = "/x"\n'
        'def _pomocnik(cel, tekst):\n'
        '    with open(cel, "a") as u:\n        u.write(tekst)\n'
        'def test_f():\n'
        '    with tempfile.TemporaryDirectory() as t:\n'
        '        _pomocnik(os.path.join(t, "a.py"), "x")\n')
    assert pomocnik_do_tymczasowego == [], (
        "skan zgłasza pomocnika wołanego ze ścieżką tymczasową: "
        f"{pomocnik_do_tymczasowego}")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
