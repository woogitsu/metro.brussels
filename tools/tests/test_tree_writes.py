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

**Ten akapit jest PRZEPISANY, a nie dopisany obok (6.D110, 10.09.2026).** Poprzednia
wersja mówiła, że bramka nie łapie zapisu przez `shutil`, `os.replace` ani
`pathlib.Path.write_text`, i to już nieprawda: od tej pozycji łapie wszystkie trzy.
Nie łapie nadal zapisu przez **podproces** i przez **bibliotekę zewnętrzną** — to jest
wprost poza zakresem 6.D110.

**Rozszerzenie nie znalazło ani jednego nowego naruszenia i to jest jego główny wynik.**
Skan po `tools/tests/` znajduje **pięć** wywołań kopiujących i przenoszących
(`shutil.copyfile` ×2, `shutil.copy2`, `os.replace` ×2) i **żadne** z nich nie celuje
w ścieżkę zbudowaną z `ROOT` — wszystkie piszą do katalogu tymczasowego albo do kopii.
Zapadka nie drgnęła. Wpis kolejki mówił o sześciu miejscach; sześć daje `grep`, który
liczy też **wiersze komentarza** cytujące te nazwy. Pięć zmierzonych miejsc stoi
wymienionych w `POZA_DRZEWEM` — nie jako wyjątki, bo nie ma czego wyjmować, tylko jako
lista rozstrzygnięć: gdy któreś z nich zacznie celować w drzewo, bramka zapali się
sama, a gdy zniknie, zapali się kontrola gnicia listy.
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

#: Wywołania kopiujące i przenoszące, z **numerem i nazwą argumentu DOCELOWEGO**.
#: Numer jest tu potrzebny, bo we wszystkich pięciu funkcjach plik pisany stoi na
#: drugim miejscu, a na pierwszym stoi plik czytany — skan biorący argument zerowy
#: meldowałby zapis tam, gdzie jest odczyt, i milczał tam, gdzie jest zapis.
#: Zbiór jest ZAMKNIĘTY i wyprowadzony z pomiaru 6.D110, nie z wyobraźni:
#: `copyfile`, `copy2` i `replace` w drzewie występują, `copy`, `move` i `rename`
#: dopisane są jako rodzeństwo o identycznej sygnaturze, bo pominięcie ich znaczyłoby,
#: że jedna litera w nazwie wyłącza bramkę.
KSZTALTY_KOPIUJACE = {
    ("shutil", "copyfile"): (1, "dst"),
    ("shutil", "copy"): (1, "dst"),
    ("shutil", "copy2"): (1, "dst"),
    ("shutil", "move"): (1, "dst"),
    ("os", "replace"): (1, "dst"),
    ("os", "rename"): (1, "dst"),
}

#: Metody `pathlib.Path` piszące do pliku, NA KTÓRYM są wołane. Celem jest tu obiekt
#: przed kropką, a nie żaden z argumentów — dlatego stoją osobno od tabeli wyżej.
METODY_SCIEZKI = ("write_text", "write_bytes")

#: Zmierzone wywołania kopiujące w `tools/tests/`, każde ze swoim
#: rozstrzygnięciem. **To nie jest lista wyjątków** — żadne z nich nie celuje w drzewo,
#: więc nie ma czego z bramki wyjmować. To lista ROZSTRZYGNIĘĆ, żądana przez pole
#: „Skończone, gdy" pozycji 6.D110, i pilnują jej dwie kontrole naraz: gdy któreś
#: z tych miejsc zacznie celować w `ROOT`, zapali się bramka główna; gdy zniknie albo
#: zmieni kształt, zapali się kontrola gnicia tej listy.
#: Znacznik ZAŚLEPKI, którą `mutation_sweep.neutralise_own_tests` podmienia
#: `test_mutation_sweep.py` w każdym drzewie roboczym przeglądu mutacyjnego. Plik
#: ZOSTAJE (jego ścieżkę wymieniają raporty), ale jego treść znika — razem z dwoma
#: wywołaniami kopiującymi, które stoją niżej w `POZA_DRZEWEM`.
#:
#: **Bez tego wyjątku bramka niżej wywracała każdy przegląd mutacyjny na kalibracji**
#: i jest to zmierzone, nie przewidziane: `mutation_sweep.py --only … --dirty` kończył
#: komunikatem „zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
#: ['test_kazde_zmierzone_kopiowanie_jest_rozstrzygniete:']". Regresja weszła
#: z 6.D110 (10.09.2026) i przeszła CI, bo CI przeglądu mutacyjnego nie uruchamia.
#: To ta sama pułapka, którą opisuje docstring `neutralise_own_tests`: bramka
#: czytająca DRZEWO widzi w drzewie roboczym co innego niż w repozytorium.
ZASLEPKA_TESTOW_SWEEPA = "test_this_file_is_the_stub_not_the_real_tests"

POZA_DRZEWEM = {
    ("test_connector_probe.py", "test_connector_probe_provenance_and_vertical_unknown", "Path.write_bytes"):
        "próbne archiwum źródła w tempfile.TemporaryDirectory",
    ("test_connector_probe.py", "test_connector_probe_provenance_and_vertical_unknown", "Path.write_text"):
        "próbny manifest i osie w tempfile.TemporaryDirectory",
    ("test_render_replay.py", "test_real_png_header", "Path.write_bytes"):
        "naglowek probnej PNG zapisywany w tempfile.TemporaryDirectory",
    ("mutation_sweep.py", "zapisz_pokrycie", "os.replace"):
        "podmiana atomowa mapy pokrycia w `tempfile.gettempdir()`",
    ("test_ci_workflows.py", "_run_blender_installer", "shutil.copyfile"):
        "instalator kopiowany do atrapy CI w katalogu tymczasowym",
    ("test_shot_metadata_gate.py",
     "test_visual_continuation_uses_independent_axis_and_glb_pair", "shutil.copyfile"):
        "niezalezna os wizualnego przedluzenia kopiowana do tempfile.TemporaryDirectory",
    ("test_dotnet_version.py", "_atrapa_dotnet_root", "shutil.copy2"):
        "atrapa układu .NET budowana w katalogu tymczasowym",
    ("test_mutation_sweep.py", "_cele_na_boku", "shutil.copyfile"):
        "cel mutacji kopiowany na bok — wzór, do którego 6.D90 przeniosło zapisy",
    ("test_mutation_sweep.py",
     "test_a_remembered_map_from_another_commit_is_refused", "os.replace"):
        "mapa przenoszona pod inną nazwę wewnątrz katalogu tymczasowego",
    ("test_mutation_sweep.py", "_dwaj_pisarze", "os.replace"):
        "wejście syntetyczne 6.D191: OBA `os.replace` idą na ścieżki zbudowane "
        "w `tempfile.TemporaryDirectory`, a drugie z nich ma prawo paść na "
        "`FileNotFoundError` — to jest mierzona połowa usterki, nie zapis do drzewa",
    ("test_provenance_classes.py",
     "test_dokument_definiujacy_status_bramki_nie_zapala", "shutil.copy"):
        "dokument modelu kopiowany do drzewa PROBNEGO w katalogu tymczasowym — "
        "6.D134 pyta skan wprost, czy definicja klasy nie jest liczona jako jej "
        "użycie, a wnioskowanie z rozszerzenia pliku okazało się niepełne",
}

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
#:
#: **Rozszerzenie skanu o trzy kształty (6.D110, ten sam dzień) NIE ruszyło tej liczby**
#: i to jest wynik pomiaru, a nie brak zmiany: pięć zmierzonych wywołań kopiujących
#: celuje co do jednego poza drzewo, więc do zapadki nie wchodzi żadne. Gdyby wchodziło,
#: zapadki i tak nie wolno by było podnieść — miejsce trzeba by przenieść na kopię.
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


def _cel_kopiowania(wezel):
    """`(kształt, węzeł celu)` dla wywołania kopiującego albo `None`.

    Jedno miejsce na rozpoznanie obu rodzin, bo obie mają odpowiadać na to samo
    pytanie: KTÓRY plik zostanie po tym wywołaniu nadpisany.
    """
    if not isinstance(wezel, ast.Call) or not isinstance(wezel.func, ast.Attribute):
        return None
    if isinstance(wezel.func.value, ast.Name):
        klucz = (wezel.func.value.id, wezel.func.attr)
        para = KSZTALTY_KOPIUJACE.get(klucz)
        if para is not None:
            numer, nazwa = para
            for slowo in wezel.keywords:
                if slowo.arg == nazwa:
                    return f"{klucz[0]}.{klucz[1]}", slowo.value
            if len(wezel.args) > numer:
                return f"{klucz[0]}.{klucz[1]}", wezel.args[numer]
            return None
    if wezel.func.attr in METODY_SCIEZKI:
        return f"Path.{wezel.func.attr}", wezel.func.value
    return None


def kopiowania_modulu(zrodlo):
    """`[(wiersz, funkcja, kształt, wyrażenie celu, czy_do_drzewa)]` — WSZYSTKIE.

    Inaczej niż `miejsca_zapisu`, ta funkcja nie odsiewa celów spoza drzewa: lista
    `POZA_DRZEWEM` ma się rozstrzygać o miejscach, które ISTNIEJĄ, a bramka główna
    widzi wyłącznie te, które celują w `ROOT`. Bez drugiego czytnika „miejsce zniknęło"
    i „miejsce przestało celować w drzewo" byłyby dla przyrządu tym samym zdarzeniem.
    """
    drzewo = ast.parse(zrodlo)
    globalne = _nazwy_od_roota(
        [w for w in drzewo.body if isinstance(w, ast.Assign)])
    out = []
    for funkcja in [w for w in ast.walk(drzewo)
                    if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        lokalne = _nazwy_od_roota([funkcja]) | globalne
        for wezel in ast.walk(funkcja):
            para = _cel_kopiowania(wezel)
            if para is None:
                continue
            ksztalt, cel = para
            odcinek = ast.unparse(cel)
            do_drzewa = bool(SLOWO_ROOT.search(odcinek)) or (
                isinstance(cel, ast.Name) and cel.id in lokalne)
            out.append((wezel.lineno, funkcja.name, ksztalt, odcinek, do_drzewa))
    return sorted(set(out))


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

        # Kształty trzeci, czwarty i piąty (6.D110): kopiowanie, przenoszenie
        # i zapis metodą `pathlib.Path`. Cel czytany jest tą samą regułą co przy
        # `open`, bo pytanie jest to samo — czy plik pisany leży w drzewie.
        for wezel in ast.walk(funkcja):
            para = _cel_kopiowania(wezel)
            if para is None:
                continue
            ksztalt, cel = para
            odcinek = _od_roota(cel)
            if odcinek is not None:
                znalezione.append((wezel.lineno, funkcja.name, odcinek, ksztalt))
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


def wszystkie_kopiowania():
    """`{moduł: [kopiowania]}` dla całego katalogu testów, bez modułów pustych."""
    out = {}
    for nazwa, sciezka in _moduly():
        with open(sciezka, encoding="utf-8") as uchwyt:
            miejsca = kopiowania_modulu(uchwyt.read())
        if miejsca:
            out[nazwa] = miejsca
    return out


def zaslepione():
    """Moduły `tools/tests/`, których treść podmieniono na zaślepkę przeglądu.

    Rozpoznanie idzie przez DRZEWO SKŁADNI, a nie przez wyszukanie napisu, i to nie
    jest ozdoba: nazwa zaślepki stoi jako zwykły tekst w `mutation_sweep.py` (wewnątrz
    `OWN_TESTS_STUB`) i w tym pliku (w stałej `ZASLEPKA_TESTOW_SWEEPA`). Skan po
    napisie uznał więc oba te moduły za zaślepione i wypuścił z bramki trzy wpisy
    zamiast dwóch — zmierzone przy pisaniu tej poprawki, w pierwszej jej wersji.
    """
    out = set()
    for nazwa, sciezka in _moduly():
        with open(sciezka, encoding="utf-8") as uchwyt:
            if jest_zaslepka(uchwyt.read()):
                out.add(nazwa)
    return out


def jest_zaslepka(zrodlo):
    """Czy ten moduł JEST zaślepką — po nazwie funkcji, nie po napisie w pliku."""
    drzewo = ast.parse(zrodlo)
    nazwy = {w.name for w in drzewo.body
             if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return ZASLEPKA_TESTOW_SWEEPA in nazwy


def test_kazde_zmierzone_kopiowanie_jest_rozstrzygniete():
    """Zmierzone wywołania kontra wpisy `POZA_DRZEWEM`, bez reszty.

    Tego żąda pole „Skończone, gdy" pozycji 6.D110: zmierzone miejsca mają być
    rozstrzygnięte, a suma rozstrzygnięć ma zgadzać się z pomiarem. Rozstrzygnięcia
    są tu dwa, nie trzy: albo cel leży poza drzewem i miejsce stoi w `POZA_DRZEWEM`,
    albo cel leży w drzewie i miejsce zapala bramkę główną. Trzeciej możliwości —
    „zmierzone, ale nikt nic z tym nie zrobił" — ta bramka nie zostawia.
    """
    znalezione = wszystkie_kopiowania()
    poza, w_drzewie = {}, {}
    for modul, miejsca in znalezione.items():
        for _wiersz, funkcja, ksztalt, cel, do_drzewa in miejsca:
            (w_drzewie if do_drzewa else poza)[(modul, funkcja, ksztalt)] = cel

    assert not w_drzewie, (
        "kopiowanie albo przenoszenie celuje w plik zbudowany ze ścieżki "
        f"repozytorium: {w_drzewie}")

    # Moduł podmieniony na zaślepkę nie jest modułem, który „zgubił" swoje wywołania:
    # jego treści w tym drzewie po prostu nie ma. Wymagać od niego wpisów znaczyłoby
    # wywracać zestaw w KAŻDYM drzewie roboczym przeglądu mutacyjnego — patrz
    # `ZASLEPKA_TESTOW_SWEEPA`.
    oczekiwane = {klucz for klucz in POZA_DRZEWEM
                  if klucz[0] not in zaslepione()}
    assert set(poza) == oczekiwane, (
        "lista rozstrzygnięć rozjechała się z drzewem — brakuje: "
        f"{sorted(set(poza) - oczekiwane)}, zbędne: "
        f"{sorted(oczekiwane - set(poza))}; moduły zaślepione: "
        f"{sorted(zaslepione()) or 'żaden'}")


def test_czytnik_rozstrzygniec_odroznia_cel_w_drzewie_od_celu_na_boku():
    """Wejście syntetyczne dla FLAGI `czy_do_drzewa` — bo na drzewie jest ona martwa.

    **To dopisała kontrola negatywna, a nie projekt bramki.** KN-7 pozycji 6.D110
    przestawiła tę flagę na stałe `False` i zestaw wyszedł **6/6, zielony**: dziś
    żadne z pięciu zmierzonych miejsc nie celuje w drzewo, więc asercja „nic nie
    celuje w drzewo" jest spełniona PUSTO i przechodzi tak samo dla czytnika
    działającego, jak dla zepsutego. Kontrola na drzewie mierzyłaby więc nie to.

    Ta sama rodzina, co KN-4 w 6.D103 i KN-3 oraz KN-6 w 6.D105: prawda pusta wygląda
    dokładnie tak samo jak prawda sprawdzona, dopóki nie poda się wejścia, na którym
    obie się rozchodzą.
    """
    w_drzewie = kopiowania_modulu(
        'import os, shutil\nROOT = "/x"\n'
        'def test_a():\n    shutil.copyfile("/z", os.path.join(ROOT, "a.py"))\n')
    assert [w[-1] for w in w_drzewie] == [True], (
        "czytnik nie widzi celu w drzewie — flaga `czy_do_drzewa` jest martwa: %r"
        % (w_drzewie,))

    na_boku = kopiowania_modulu(
        'import os, shutil, tempfile\nROOT = "/x"\n'
        'def test_b():\n'
        '    with tempfile.TemporaryDirectory() as t:\n'
        '        shutil.copyfile(os.path.join(ROOT, "a.py"), os.path.join(t, "a.py"))\n')
    assert [w[-1] for w in na_boku] == [False], (
        "czytnik uznaje cel w katalogu tymczasowym za cel w drzewie: %r" % (na_boku,))


def test_zaslepka_rozpoznaje_sie_po_definicji_a_nie_po_napisie():
    """Wejście syntetyczne dla obu kierunków rozpoznania zaślepki.

    Pierwsza wersja tej poprawki szukała nazwy zaślepki jako NAPISU i uznała za
    zaślepione trzy moduły zamiast zera — bo ta sama nazwa stoi jako zwykły tekst
    w `mutation_sweep.py` (w stałej `OWN_TESTS_STUB`) i w tym pliku. Bramka
    wypuszczała wtedy z listy rozstrzygnięć wpisy, które w drzewie są.
    """
    zaslepka = ("\"\"\"Zaślepka.\"\"\"\n\n\n"
                "def %s():\n    assert True\n" % ZASLEPKA_TESTOW_SWEEPA)
    assert jest_zaslepka(zaslepka), "zaślepka nie została rozpoznana"

    cytujacy = ('ZASLEPKA = "%s"\n\n\n'
                "def test_cos():\n    assert True\n" % ZASLEPKA_TESTOW_SWEEPA)
    assert not jest_zaslepka(cytujacy), (
        "moduł CYTUJĄCY nazwę zaślepki został uznany za zaślepkę — to jest ta "
        "pomyłka, którą zrobiła pierwsza wersja tej poprawki")

    # **Asercji „w repozytorium nie ma zaślepki" tu NIE MA i to jest wybór z pomiaru.**
    # Pierwsza wersja tego testu ją miała i zachowywała się dokładnie tak, jak usterka,
    # którą ta poprawka zamyka: w repozytorium zielona, a w KAŻDYM drzewie roboczym
    # przeglądu mutacyjnego czerwona — bo tam zaślepka leży z definicji. Zmierzone na
    # kopii drzewa po `neutralise_own_tests`: 7/8, zgłoszenie „w repozytorium leży
    # zaślepka przeglądu mutacyjnego: ['test_mutation_sweep.py']".
    assert not jest_zaslepka(""), "pusty moduł nie jest zaślepką"


def test_skan_kopiowan_widzi_ksztalt_ktory_ma_widziec():
    """Trzy nowe kształty, każdy na DWÓCH wejściach: cel z `ROOT` i cel tymczasowy.

    Wejście z celem tymczasowym nie jest ozdobą: skan, który zapala się na wszystkim,
    jest tak samo bezużyteczny jak ślepy, a odróżnić jednego od drugiego da się
    wyłącznie parą. Tego żąda pole „Skończone, gdy" pozycji 6.D110 wprost.
    """
    def skan(tresc):
        return miejsca_zapisu("import os, shutil, tempfile, pathlib\nROOT = \"/x\"\n"
                              + tresc)

    kopia_do_drzewa = skan(
        'def test_a():\n    shutil.copyfile("/z", os.path.join(ROOT, "a.py"))\n')
    assert len(kopia_do_drzewa) == 1, (
        "skan nie widzi `shutil.copyfile` celującego w drzewo: %r" % (kopia_do_drzewa,))
    kopia_na_bok = skan(
        'def test_b():\n'
        '    with tempfile.TemporaryDirectory() as t:\n'
        '        shutil.copyfile(os.path.join(ROOT, "a.py"), os.path.join(t, "a.py"))\n')
    assert kopia_na_bok == [], (
        "skan bierze plik CZYTANY za pisany — to dokładnie ten kształt, w którym "
        f"stoją wszystkie pięć zmierzonych miejsc: {kopia_na_bok}")

    przenoszenie_do_drzewa = skan(
        'def test_c():\n    os.replace("/z", os.path.join(ROOT, "a.py"))\n')
    assert len(przenoszenie_do_drzewa) == 1, (
        "skan nie widzi `os.replace` celującego w drzewo: %r" % (przenoszenie_do_drzewa,))
    przenoszenie_na_bok = skan(
        'def test_d():\n'
        '    with tempfile.TemporaryDirectory() as t:\n'
        '        os.replace(os.path.join(t, "a"), os.path.join(t, "b"))\n')
    assert przenoszenie_na_bok == [], (
        "skan zgłasza przeniesienie w obrębie katalogu tymczasowego: %r"
        % (przenoszenie_na_bok,))

    sciezka_do_drzewa = skan(
        'def test_e():\n'
        '    pathlib.Path(os.path.join(ROOT, "a.py")).write_text("x")\n')
    assert len(sciezka_do_drzewa) == 1, (
        "skan nie widzi `pathlib.Path.write_text` na ścieżce z drzewa: %r"
        % (sciezka_do_drzewa,))
    sciezka_na_bok = skan(
        'def test_f():\n'
        '    with tempfile.TemporaryDirectory() as t:\n'
        '        pathlib.Path(os.path.join(t, "a.py")).write_bytes(b"x")\n')
    assert sciezka_na_bok == [], (
        "skan zgłasza `write_bytes` do katalogu tymczasowego: %r" % (sciezka_na_bok,))

    # Cel podany SŁOWEM KLUCZOWYM. Bez tego kształtu bramkę wyłączałoby przestawienie
    # argumentu na nazwany, a to jest zmiana czysto redakcyjna.
    przez_slowo = skan(
        'def test_g():\n    shutil.copyfile("/z", dst=os.path.join(ROOT, "a.py"))\n')
    assert len(przez_slowo) == 1, (
        f"skan nie widzi celu podanego słowem kluczowym: {przez_slowo}")

    # Zmienna pośrednia, ten sam kształt co przy `open` — cel liczony u WOŁAJĄCEGO.
    przez_zmienna = skan(
        'def test_h():\n'
        '    pelna = os.path.join(ROOT, "a.py")\n'
        '    shutil.copy2("/z", pelna)\n')
    assert len(przez_zmienna) == 1, (
        "skan nie widzi celu podanego przez zmienną pośrednią: %r"
        % (przez_zmienna,))


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
