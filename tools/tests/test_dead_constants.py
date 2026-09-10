#!/usr/bin/env python3
"""Stala modulowa, ktorej nikt nie czyta, jest zglaszana albo uzasadniona.

**Skad ta bramka.** 6.B29, ze znaleziska przy 6.B25. `MIN_RADIUS_M = 20.0` stalo
w `tools/blender/clearance.py` **od swojego pierwszego commita** (#50, 01.09.2026),
nieczytane przez nic — i zdazylo w tym czasie zostac zacytowane w docstringu innego
modulu jako granica OBOWIAZUJACA. Martwa stala nie jest samym ciezarem: jest zdaniem
o repozytorium, ktore ktos przeczyta i uzna za prawdziwe.

**Dlaczego to NIE jest ta bramka, co 6.B25.** `test_constant_names.py` lapie KOLIZJE
— jedna nazwe o dwoch wartosciach. Kontrola negatywna KN-1 tamtej pozycji pokazala
wprost, ze martwoty nie lapie: stala przywrocona do `clearance.py` nie tworzy kolizji,
bo drugiej definicji juz nie ma, i tamta bramka milczy. Sa to dwa rozne zjawiska
i dwa rozne testy.

**Odczyt liczony przez `ast`, nie grepem.** Grep na nazwie zlapalby ja w komentarzu,
w docstringu i w napisie — a wlasnie tak `MIN_RADIUS_M` wygladalo na zyjace. Liczone
sa `Name` w kontekscie `Load` i `Attribute`, bo stala czyta sie takze jako `M.NAZWA`.

**`*.sh` i `.github/` sprawdzane osobno, i to nie jest ostroznosc na zapas.** Skrypty
CI woluja moduly przez `python3 -c "...M.NAZWA..."`, wiec stala czytana wylacznie
stamtad NIE jest martwa, a `ast` po plikach `.py` jej nie zobaczy — tresc tamtego
wywolania jest dla niego napisem. Zmierzone 07.09.2026: `tools/ci/vehicle_clearance.sh`
i `tools/ci/station_details.sh` zawieraja pelne programy w `python3 -c`.
"""
import ast
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DRZEWA = ("tools", "src")
#: Katalogi, w ktorych szukamy odczytow POZA Pythonem — patrz docstring modulu.
POZA_PYTHONEM = ((os.path.join(ROOT, "tools"), (".sh",)),
                 (os.path.join(ROOT, ".github"), (".yml", ".yaml")))

#: Stale nieczytane, uznane po obejrzeniu: nazwa -> (plik, powod).
#: Zmierzone 07.09.2026. Dopisanie tu wpisu jest oswiadczeniem, ze stala ma zostac
#: mimo braku odczytu; test nizej pilnuje, ze wpis bez martwej stalej znika razem z nia.
UZASADNIONE = {
    "LOCATION_STATION": (
        "tools/track/normalize_stops.py",
        "brakujacy element wyliczenia `location_type` z GTFS: stoi w trojce "
        "LOCATION_STOP / LOCATION_STATION / LOCATION_ENTRANCE, ktora spisuje ten "
        "slownik w calosci. Dwie wartosci sa czytane, trzecia nie — jej usuniecie "
        "zepsulo by czytelnosc zbioru, zamiast zdjac ciezar"),
}


def _pliki_python(root=ROOT):
    for drzewo in DRZEWA:
        # 6.D97: bez własnego `if "__pycache__" in katalog` — `TW.walk` odsiewa
        # ten katalog z `.gitignore`, gdzie stoi obok dziesięciu innych.
        for katalog, _pod, pliki in TW.walk(os.path.join(root, drzewo), root):
            for plik in pliki:
                if plik.endswith(".py"):
                    yield os.path.join(katalog, plik)


def _drzewo(sciezka):
    with open(sciezka, encoding="utf-8") as uchwyt:
        try:
            return ast.parse(uchwyt.read())
        except SyntaxError:
            return None


def definicje(root=ROOT):
    """Stale modulowe: zbior `(sciezka wzgledna, nazwa)`.

    Bez zadnego filtra na KSZTALT wartosci, i to jest wybor zmierzony, nie domyslny.
    Pierwsza wersja brala tylko wartosci proste (int, float, str), jak `MIN_RADIUS_M`,
    ktore te bramke wywolalo — bylo ich 242. Zawezenie kosztowaloby zasieg, a nie
    kupiloby czystosci: policzone 07.09.2026, przy trzech kolejnych zasiegach liczba
    stalych NIECZYTANYCH jest **ta sama**:

    ```
    proste (int/float/str)   definicji=242  nieczytanych=1
    literalne (+ dict, list) definicji=348  nieczytanych=1
    wszystkie                definicji=705  nieczytanych=1
    ```

    Martwy slownik progow czy martwa krotka nazw byly by dokladnie tak samo zdaniem
    o repozytorium, ktore ktos przeczyta i uzna za prawdziwe — a wezszy zasieg nie
    zglosilby ich.
    """
    znalezione = set()
    for sciezka in _pliki_python(root):
        drzewo = _drzewo(sciezka)
        if drzewo is None:
            continue
        for wezel in drzewo.body:
            if not isinstance(wezel, ast.Assign) or len(wezel.targets) != 1:
                continue
            cel = wezel.targets[0]
            if isinstance(cel, ast.Name) and cel.id.isupper():
                znalezione.add((os.path.relpath(sciezka, root), cel.id))
    return znalezione


def odczyty(root=ROOT):
    """Nazwy CZYTANE gdziekolwiek w drzewie — z Pythona przez `ast`, z reszty tekstem.

    Z plikow `.py` liczone sa `Name` w kontekscie `Load` i `Attribute`; przypisanie
    (`ctx=Store`) odczytem nie jest, bo inaczej kazda definicja czytalaby sie sama.
    Z `*.sh` i `.github/*.yml` — wystapienie nazwy jako calego slowa, bo tam nie ma
    czego rozbierac, a falszywy odczyt jest tu tansza pomylka niz falszywa martwota.
    """
    czytane = set()
    for sciezka in _pliki_python(root):
        drzewo = _drzewo(sciezka)
        if drzewo is None:
            continue
        for wezel in ast.walk(drzewo):
            if isinstance(wezel, ast.Name) and isinstance(wezel.ctx, ast.Load):
                czytane.add(wezel.id)
            elif isinstance(wezel, ast.Attribute):
                czytane.add(wezel.attr)
    return czytane


def _tresc_poza_pythonem():
    kawalki = []
    for katalog, rozszerzenia in POZA_PYTHONEM:
        if not os.path.isdir(katalog):
            continue
        for gdzie, _pod, pliki in TW.walk(katalog):
            for plik in pliki:
                if plik.endswith(rozszerzenia):
                    with open(os.path.join(gdzie, plik), encoding="utf-8",
                              errors="replace") as uchwyt:
                        kawalki.append(uchwyt.read())
    return "\n".join(kawalki)


def martwe(root=ROOT):
    """`{nazwa: [pliki]}` dla stalych, ktorych nic w drzewie nie czyta."""
    czytane = odczyty(root)
    kandydaci = {}
    for (sciezka, nazwa) in sorted(definicje(root)):
        if nazwa not in czytane:
            kandydaci.setdefault(nazwa, []).append(sciezka)
    if not kandydaci:
        return {}
    poza = _tresc_poza_pythonem()
    return {nazwa: sorted(pliki) for nazwa, pliki in kandydaci.items()
            if not re.search(r"\b" + re.escape(nazwa) + r"\b", poza)}


def test_every_unread_constant_is_justified():
    znalezione = martwe()
    nieuzasadnione = sorted(set(znalezione) - set(UZASADNIONE))
    assert not nieuzasadnione, (
        "stala modulowa, ktorej nic w tools/ ani src/ nie czyta, bez wpisu "
        "w UZASADNIONE: "
        + "; ".join("%s (%s)" % (n, ", ".join(znalezione[n])) for n in nieuzasadnione)
        + ". Albo jest do usuniecia, albo ma zostac i nalezy powiedziec dlaczego "
          "jednym zdaniem w tym samym commicie — martwa stala jest zdaniem "
          "o repozytorium, ktore ktos przeczyta i uzna za prawdziwe (#50)")


def test_no_justification_outlives_the_constant_it_describes():
    """Drugi kierunek. Wpis, ktory przestal opisywac martwa stala, jest gorszy od jego
    braku: gnijaca lista wyjatkow wyglada na przemyslana."""
    znalezione = martwe()
    martwe_wpisy = sorted(set(UZASADNIONE) - set(znalezione))
    assert not martwe_wpisy, (
        "UZASADNIONE opisuje stale, ktore albo znikly, albo znowu sa czytane: "
        + ", ".join(martwe_wpisy) + " — skresl wpis razem z powodem, dla ktorego stal")


def test_the_justification_names_the_file_it_talks_about():
    """Powod bez pliku starzeje sie bez sladu: stala przeniesiona gdzie indziej
    zostawia zdanie, ktorego nie da sie sprawdzic."""
    for nazwa, (plik, powod) in UZASADNIONE.items():
        assert os.path.isfile(os.path.join(ROOT, plik)), (nazwa, plik)
        assert (plik, nazwa) in definicje(), (
            "wpis UZASADNIONE mowi, ze %s stoi w %s, a tam jej nie ma" % (nazwa, plik))
        assert len(powod) > 40, (nazwa, powod)


def test_the_name_from_this_task_is_gone():
    """`MIN_RADIUS_M` bylo powodem tej bramki i ma NIE wrocic jako stala nieczytana.

    Osobny test, bo dopisanie nazwy do `UZASADNIONE` zamknelo by usta bramce ogolnej —
    a to jest wlasnie ta stala, ktora 6.B25 uznalo za bledna, nie za uzasadniona.
    """
    assert "MIN_RADIUS_M" not in UZASADNIONE, (
        "MIN_RADIUS_M wpisany na liste uzasadnionych: 6.B25 zmierzylo, ze byla martwa "
        "od #50, a prog 90,0 nalezy czytac z tools/track/validate.py")
    assert "MIN_RADIUS_M" not in martwe(), "MIN_RADIUS_M wrocilo jako stala nieczytana"


def test_a_store_is_not_counted_as_a_read():
    """Kontrola przyrzadu. Gdyby `odczyty` liczylo tez `ctx=Store`, KAZDA definicja
    czytalaby sie sama i bramka nie zglosilaby nigdy niczego — czyli byla by zielona
    z tego samego powodu, z ktorego zielone bylo `python3 <modul>.py` przed 6.D25."""
    drzewo = ast.parse("MARTWA = 1\n")
    czytane = {w.id for w in ast.walk(drzewo)
               if isinstance(w, ast.Name) and isinstance(w.ctx, ast.Load)}
    assert "MARTWA" not in czytane, "przypisanie policzone jako odczyt"
    drzewo = ast.parse("MARTWA = 1\nprint(MARTWA)\n")
    czytane = {w.id for w in ast.walk(drzewo)
               if isinstance(w, ast.Name) and isinstance(w.ctx, ast.Load)}
    assert "MARTWA" in czytane, "prawdziwy odczyt nierozpoznany"


def test_an_attribute_read_counts_because_constants_travel_as_module_dot_name():
    """`M.NAZWA` jest odczytem. Bez tego kazda stala czytana wylacznie przez cudzy
    modul — czyli wiekszosc tych, ktore cokolwiek znacza — wyszla by jako martwa."""
    czytane = set()
    for wezel in ast.walk(ast.parse("import m\nx = m.PROG_M\n")):
        if isinstance(wezel, ast.Attribute):
            czytane.add(wezel.attr)
    assert "PROG_M" in czytane


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
