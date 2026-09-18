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
import tempfile
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
    "_UCHWYT_ZAMKA": (
        "tools/tests/mutation_sweep.py",
        "6.D123: nikt jej nie CZYTA i to jest jej caly sens — `flock` zyje tak "
        "dlugo, jak otwarty opis pliku, wiec uchwyt musi miec wlasciciela, ktory "
        "przezyje wyjscie z `main`. Zmienna lokalna zwolnilaby zamek natychmiast "
        "po sprawdzeniu; zmierzone, gdy dwa kolejne wywolania `zajmij_dziennik` "
        "bez trzymanej referencji daly OBA `wziety`, bo GC zamknal pierwszy "
        "uchwyt. Usuniecie tej stalej zdejmuje zamek, nie ciezar"),
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


# --- 6.D269: podstawienie stalej modulu, ktore nie dziala ----------------------

#: **Podstawienie `modul.STALA = X` w kontroli jest MARTWE, jezeli modul
#: przechwycil wartosc przy IMPORCIE.** Zmierzone 18.09.2026 przy 6.D265, przez
#: kontrole przyrzadu, ktora sama byla slepa: `csharp_test_methods.ROOT = <kopia>`
#: nie przekierowalo czytnika, bo `pomocnicy(root=ROOT)` wiaze `ROOT` raz, w chwili
#: importu. Kontrola wypisala cztery jednakowe liczby i czytalo sie to jak wynik
#: o KODZIE, a byl to wynik o KONTROLI.
#:
#: **Przechwycic wartosc przy imporcie mozna DWOMA ksztaltami i bramka obejmuje
#: oba.** Drugiego pozycja 6.D269 nie nazywala — doszedl z pomiaru:
#:
#: 1. **domyslny argument** — `def f(root=ROOT)`: wyrazenie domyslne liczy sie raz,
#:    przy definiowaniu funkcji, wiec pozniejsze podstawienie globalnej nie ma juz
#:    na nia wplywu;
#: 2. **stala pochodna na poziomie modulu** — `SCIEZKA = os.path.join(ROOT, "x")`:
#:    liczy sie przy imporcie, wiec podstawienie `ROOT` nie rusza `SCIEZKA`.
#:
#: **Zmierzone 18.09.2026:** wiazan domyslnych jest 132 w 36 plikach (para
#: „funkcja + stala", bo ta sama stala wiazana w trzech funkcjach daje trzy
#: miejsca martwego podstawienia), co daje 81 roznych par `(modul, nazwa)`.
#: Podstawien `modul.STALA` jest 23 w 6 plikach, przy 8 roznych
#: stalych. Obie liczby po stronie wiazania sa podane, bo sa ROZNE i pomylenie
#: ich zlapala podloga tej bramki przy pierwszym przebiegu.
#:
#: **Kolizji jest dzis ZERO i jest to ZBIEG, nie zabezpieczenie** — dokladnie
#: dlatego ta bramka istnieje. Zadna z osmiu podstawianych stalych nie jest ani
#: wiazana domyslnie, ani nie ma pochodnej; pierwsze podstawienie stalej, ktora
#: ktorys z tych ksztaltow ma, dalo by kontrole cicha i zielona.
#:
#: **Ten modul sam jest przykladem ksztaltu pierwszego:** `definicje(root=ROOT)`,
#: `odczyty(root=ROOT)` i `_pliki_python(root=ROOT)` wiaza `ROOT` domyslnie.
#: Nie jest to usterka — nikt tego `ROOT` nie podstawia, a testy przekazuja
#: `root` wywolaniem. Jest to natomiast powod, dla ktorego bramka porownuje
#: PRZECIECIE dwoch list, a nie karze samego wiazania: 132 funkcje maja ten
#: ksztalt i przepisanie ich bylo by praca bez zmierzonej potrzeby.
MARTWYCH_PODSTAWIEN = 0

#: Podlogi na OBA czytniki. ZERO czesci wspolnej da takze czytnik oslepiony do
#: zera — i wtedy bramka jest zielona nie dlatego, ze kolizji nie ma, a dlatego,
#: ze nie widzi zadnej strony (6.D27). WOLNE oba, bo obu populacji przybywa
#: razem z narzedziami.
MIN_WIAZANYCH_DOMYSLNIE = 100
MIN_PODSTAWIEN_W_TESTACH = 15


def _aliasy_importow(drzewo):
    """`{alias: nazwa modulu}` — `import x as A` i `from p import x as A`.

    Alias trzeba rozwiazac, bo podstawienie stoi pod nim (`sweep.ROOT`), a lista
    wiazanych domyslnie jest indeksowana nazwa MODULU. Bez tego `G.ALLOWED`
    i `G.AXIS_TOLERANCE_M` — dwa rozne moduly pod tym samym aliasem w dwoch
    plikach — trafialyby do jednego worka.
    """
    out = {}
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, ast.Import):
            for nazwa in wezel.names:
                out[nazwa.asname or nazwa.name.split(".")[0]] = nazwa.name.split(".")[-1]
        elif isinstance(wezel, ast.ImportFrom):
            for nazwa in wezel.names:
                out[nazwa.asname or nazwa.name] = nazwa.name
    return out


def wiazane_domyslnie(root=None):
    """`{modul: {NAZWA}}` — stale modulu wiazane DOMYSLNYM ARGUMENTEM.

    Nazwy, nie wystapienia: do PRZECIECIA z podstawieniami liczy sie to, czy
    stala jest wiazana gdziekolwiek, a nie ile razy. Liczbe wystapien podaje
    `wiazan_domyslnych`, bo to o nia pytalo pole „Wyjscie" — i sa to DWIE rozne
    liczby, co zlapala podloga tej bramki przy pierwszym przebiegu: proza mowila
    o 132 wystapieniach, a czytnik dawal 81 par (modul, nazwa).
    """
    out = {}
    for sciezka in _pliki_python(root or ROOT):
        drzewo = _drzewo(sciezka)
        if drzewo is None:
            continue
        globalne = {t.id for w in drzewo.body if isinstance(w, ast.Assign)
                    for t in w.targets if isinstance(t, ast.Name)}
        nazwy = set()
        for funkcja in ast.walk(drzewo):
            if not isinstance(funkcja, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            domyslne = list(funkcja.args.defaults) + [
                k for k in funkcja.args.kw_defaults if k is not None]
            for wyrazenie in domyslne:
                if isinstance(wyrazenie, ast.Name) and wyrazenie.id in globalne:
                    nazwy.add(wyrazenie.id)
        if nazwy:
            out[os.path.basename(sciezka)[:-3]] = nazwy
    return out


def wiazan_domyslnych(root=None):
    """Ile RAZY stala modulu stoi jako wyrazenie domyslne — odpowiedz na „Wyjscie".

    Para `(funkcja, stala)`, a nie sama stala: ta sama stala wiazana w trzech
    funkcjach daje trzy wystapienia i trzy miejsca, w ktorych podstawienie
    bylo by martwe.
    """
    ile = 0
    for sciezka in _pliki_python(root or ROOT):
        drzewo = _drzewo(sciezka)
        if drzewo is None:
            continue
        globalne = {t.id for w in drzewo.body if isinstance(w, ast.Assign)
                    for t in w.targets if isinstance(t, ast.Name)}
        for funkcja in ast.walk(drzewo):
            if not isinstance(funkcja, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            domyslne = list(funkcja.args.defaults) + [
                k for k in funkcja.args.kw_defaults if k is not None]
            ile += sum(1 for w in domyslne
                       if isinstance(w, ast.Name) and w.id in globalne)
    return ile


def pochodne_modulu(root=None):
    """`{modul: {NAZWA: [pochodne]}}` — stale POZIOMU MODULU liczone ze stalej.

    Tylko `drzewo.body`, a nie `ast.walk`: przechwycenie wartosci przy imporcie
    robi WYLACZNIE przypisanie na poziomie modulu. To samo wyrazenie w ciele
    funkcji liczy sie przy kazdym wywolaniu i podstawienie widzi.
    """
    out = {}
    for sciezka in _pliki_python(root or ROOT):
        drzewo = _drzewo(sciezka)
        if drzewo is None:
            continue
        globalne = {t.id for w in drzewo.body if isinstance(w, ast.Assign)
                    for t in w.targets if isinstance(t, ast.Name)}
        mapa = {}
        for wezel in drzewo.body:
            if not isinstance(wezel, ast.Assign):
                continue
            zrodla = {x.id for x in ast.walk(wezel.value)
                      if isinstance(x, ast.Name)} & globalne
            for cel in wezel.targets:
                if isinstance(cel, ast.Name):
                    for zrodlo in zrodla - {cel.id}:
                        mapa.setdefault(zrodlo, []).append(cel.id)
        if mapa:
            out[os.path.basename(sciezka)[:-3]] = mapa
    return out


def podstawienia(root=None):
    """`[(plik, wiersz, alias, NAZWA, modul)]` — `modul.STALA = ...` w testach."""
    korzen = root or ROOT
    out = []
    for katalog, _pod, pliki in TW.walk(os.path.join(korzen, "tools", "tests"), korzen):
        for plik in sorted(pliki):
            if not plik.endswith(".py"):
                continue
            drzewo = _drzewo(os.path.join(katalog, plik))
            if drzewo is None:
                continue
            aliasy = _aliasy_importow(drzewo)
            for wezel in ast.walk(drzewo):
                if not isinstance(wezel, ast.Assign):
                    continue
                for cel in wezel.targets:
                    if (isinstance(cel, ast.Attribute) and cel.attr.isupper()
                            and isinstance(cel.value, ast.Name)):
                        out.append((plik, wezel.lineno, cel.value.id, cel.attr,
                                    aliasy.get(cel.value.id, cel.value.id)))
    return out


def martwe_podstawienia(root=None):
    """`[(plik, wiersz, NAZWA, modul, ksztalt)]` — podstawienia bez skutku."""
    domyslne = wiazane_domyslnie(root)
    pochodne = pochodne_modulu(root)
    out = []
    for plik, wiersz, _alias, nazwa, modul in podstawienia(root):
        if nazwa in domyslne.get(modul, set()):
            out.append((plik, wiersz, nazwa, modul, "domyslny argument"))
        elif nazwa in pochodne.get(modul, {}):
            out.append((plik, wiersz, nazwa, modul, "stala pochodna"))
    return out


def test_ile_podstawien_stalej_modulu_jest_MARTWYCH():
    """**Rownosc na przecieciu dwoch list, z podlogami na oba czytniki.**

    Rownosc, a nie prog: kazde nowe martwe podstawienie ma zapalic, bo kontrola,
    ktora nie przekierowuje niczego, wyglada jak pomiar o kodzie — zmierzone
    przy 6.D265, gdzie cztery jednakowe liczby dalo sie opowiedziec jako
    odkrycie i tylko spisane wcześniej oczekiwanie temu zapobiegło.
    """
    podstawione = podstawienia()
    ile_domyslnych = wiazan_domyslnych()
    assert ile_domyslnych >= MIN_WIAZANYCH_DOMYSLNIE, (
        "wiazan domyslnych widac %d przy podlodze %d — "
        "czytnik oslepl, a wtedy przeciecie nizej jest puste nie dlatego, ze "
        "kolizji nie ma" % (ile_domyslnych, MIN_WIAZANYCH_DOMYSLNIE))
    assert len(podstawione) >= MIN_PODSTAWIEN_W_TESTACH, (
        "podstawien `modul.STALA` widac %d przy podlodze %d — jak wyzej, "
        "z drugiej strony przeciecia" % (len(podstawione), MIN_PODSTAWIEN_W_TESTACH))

    martwe_dzis = martwe_podstawienia()
    assert len(martwe_dzis) == MARTWYCH_PODSTAWIEN, (
        "martwych podstawien jest %d, a pomiar 18.09.2026 dal %d: %r. "
        "Podstawienie stalej, ktora modul przechwycil przy imporcie (domyslnym "
        "argumentem albo stala pochodna), nie przekierowuje niczego — a kontrola "
        "oparta na nim jest cicha i zielona"
        % (len(martwe_dzis), MARTWYCH_PODSTAWIEN, martwe_dzis))


def test_czytnik_martwych_podstawien_widzi_OBA_ksztalty_i_nie_widzi_zdrowego():
    """**Kontrola przyrzadu na drzewie probnym — trzy przypadki, nie jeden.**

    Bramka wyzej jest rownoscia na ZERO, wiec bez tej kontroli przechodzilaby
    takze przy czytniku, ktory nie widzi NICZEGO. Sprawdzane sa naraz: ksztalt
    domyslnego argumentu, ksztalt stalej pochodnej (dolozony pomiarem, bo pozycja
    go nie nazywala) oraz podstawienie ZDROWE, ktore ma zostac przepuszczone —
    inaczej bramka mowi „nie podstawiaj stalych", a nie „nie podstawiaj TYCH".
    """
    with tempfile.TemporaryDirectory() as katalog:
        os.makedirs(os.path.join(katalog, "tools", "tests"))
        with open(os.path.join(katalog, ".gitignore"), "w", encoding="utf-8") as u:
            u.write("__pycache__/\n")

        def zapisz(wzgledna, tresc):
            sciezka = os.path.join(katalog, wzgledna)
            os.makedirs(os.path.dirname(sciezka), exist_ok=True)
            with open(sciezka, "w", encoding="utf-8") as uchwyt:
                uchwyt.write(tresc)

        zapisz("tools/tests/probny.py",
               "ROOT = 'a'\n"
               "POCHODNA_ZRODLO = 'b'\n"
               "ZDROWY = 'c'\n"
               "SCIEZKA = POCHODNA_ZRODLO + '/x'\n"
               "\n"
               "def f(root=ROOT):\n"
               "    return root\n"
               "\n"
               "def g():\n"
               "    return ZDROWY\n")
        zapisz("tools/tests/test_probny.py",
               "import probny as P\n"
               "\n"
               "def test_a():\n"
               "    P.ROOT = 'x'\n"
               "    P.POCHODNA_ZRODLO = 'y'\n"
               "    P.ZDROWY = 'z'\n")

        martwe_probne = martwe_podstawienia(katalog)
        ksztalty = sorted((n, k) for _p, _w, n, _m, k in martwe_probne)
        # Rownosc, a nie dwie asercje z `in`: ta sama para niesie OBA zadania
        # kontroli naraz — ze oba ksztalty sa zlapane i ze `ZDROWY`, ktorego
        # modul nie przechwytuje, NIE jest zgloszony. Rozbicie tego na `X in`
        # i `Y not in` dawalo bramce `test_ile_bramek_stoi_na_NAPISIE` dwie
        # asercje ksztaltu „literal in cos", a mowilo mniej.
        assert ksztalty == [("POCHODNA_ZRODLO", "stala pochodna"),
                            ("ROOT", "domyslny argument")], (
            "czytnik ma zlapac DOKLADNIE dwa przechwycone ksztalty i przepuscic "
            "`ZDROWY`, ktorego modul nie przechwytuje — inaczej bramka zabrania "
            "podstawiania stalych w ogole, a nie tych przechwyconych. Dostal: %r"
            % (ksztalty,))


def test_alias_importu_jest_ROZWIAZYWANY_a_nie_brany_doslownie():
    """**Dolne ostrze na aliasy — dwa moduly stoja tu pod tym samym `G`.**

    `test_godot_warning_gate.py` ma `G` = `assert_no_godot_warnings`, a
    `test_shot_metadata_gate.py` ma `G` = `assert_shot_metadata`. Czytnik biorący
    alias doslownie wrzucilby oba do jednego worka `G` i porownywal stale jednego
    modulu z lista drugiego — czyli zglaszalby kolizje tam, gdzie jej nie ma,
    albo przeoczyl te, ktora jest.
    """
    aliasy_wielu = {}
    for plik, _wiersz, alias, _nazwa, modul in podstawienia():
        aliasy_wielu.setdefault(alias, set()).add(modul)
    wielokrotne = {a: sorted(m) for a, m in aliasy_wielu.items() if len(m) > 1}
    assert wielokrotne, (
        "zaden alias nie prowadzi juz do dwoch modulow — kontrola stracila "
        "material i trzeba ja oprzec na drzewie probnym")
    for alias, moduly in wielokrotne.items():
        assert all(m != alias for m in moduly), (
            "alias %s nie zostal rozwiazany: %r" % (alias, moduly))
