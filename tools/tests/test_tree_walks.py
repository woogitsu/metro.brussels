#!/usr/bin/env python3
"""Przejście po drzewie nie wchodzi w kopie pominięte w `.gitignore` (6.D74).

**Skąd ta bramka.** Zmierzone 09.09.2026 przy 6.D36: pierwszy skan tamtej pozycji,
liczony od korzenia, dał **6 i 12** wystąpień zamiast 1 i 2, bo wszedł do kopii drzewa
leżącej pod `.claude/`. Kopie niosły STARY kod, więc skan raportowałby usterkę już
naprawioną — przyrząd meldujący sprawdzenie, którego nie zrobił.

**Dlaczego pozycja, choć dziś prawie nic nie pada.** Trzynaście z czternastu wywołań
`os.walk` w `tools/` startowało z NAZWANEGO podkatalogu, a kopie 6.D36 leżały pod
`.claude/` — ochrona była **uboczna wobec nazewnictwa**, nie zapisana. Jedno przejście
liczone od korzenia wywraca wszystkie naraz i nic tego nie zgłasza.

**„Prawie nic" nie znaczy „nic", i to jest wynik pomiaru.** Kopia drzewa położona
10.09.2026 pod `tools/build/kopia/` (`build/` stoi w `.gitignore`, więc git jej nie
widzi, a `os.walk` owszem) zmieniła **jedną z piętnastu** liczb raportowanych przez
skany: `test_dead_constants.definicje` **917 → 1511**. Pozostałe czternaście stały,
bo albo startują poza `tools/`, albo zwracają ZBIÓR nazw, w którym kopia niczego
nowego nie wnosi. Jedna nieprawdziwa liczba w drzewie jest powodem wystarczającym.
"""
import ast
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

#: Pliki, w których `os.walk` wolno zawołać WPROST, z powodem. Klucz to ścieżka
#: względem korzenia, zapisana ukośnikami. Wpisów są dwa i oba są konieczne, a nie
#: wygodne: bez pierwszego nie ma czego wołać, bez drugiego nie da się POKAZAĆ, że
#: odsianie cokolwiek odsiewa — dowodem jest różnica wobec przejścia gołego.
WOLNO_WPROST = {
    "tools/tests/tree_walk.py":
        "to jest samo odsianie: `TW.walk` jest cienką warstwą nad `os.walk` "
        "i nie ma jak owinąć siebie.",
    "tools/tests/test_tree_walks.py":
        "kontrola różnicy: `test_the_filter_skips_a_branch_that_os_walk_enters` "
        "puszcza OBA przejścia po tym samym drzewie probnym i żąda, żeby wynik "
        "był różny. Przejście gołe jest tam PRZEDMIOTEM pomiaru, nie skrótem.",
}

#: Zapadka na słownik wyżej. Wolno ją tylko OBNIŻAĆ — ta sama reguła, co przy
#: `MAX_EXCEPTIONS` w `test_field_paths.py`: wyjątek jest tańszym wyjściem niż
#: przepisanie wołania, więc lista rośnie w jedną stronę z definicji.
MAX_WOLNO_WPROST = 2

#: Drzewa przeszukiwane w poszukiwaniu wywołań.
DRZEWA = ("tools",)


def _pliki_python():
    for drzewo in DRZEWA:
        for katalog, _pod, pliki in TW.walk(os.path.join(ROOT, drzewo)):
            for plik in sorted(pliki):
                if plik.endswith(".py"):
                    yield os.path.relpath(os.path.join(katalog, plik), ROOT)


def wywolania_os_walk():
    """`(plik, wiersz)` każdego wołania `os.walk` — z drzewa składni, nie z grepa.

    Grep po napisie `os.walk(` łapie też docstringi i komentarze, a w tym projekcie
    stoi tam pół tuzina zdań O `os.walk` — czyli miejsca, w których przejście jest
    OPISANE, a nie wykonane.
    """
    found = []
    for relative in _pliki_python():
        try:
            drzewo = ast.parse(open(os.path.join(ROOT, relative), encoding="utf-8").read())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(drzewo):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "walk"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"):
                found.append((relative.replace(os.sep, "/"), node.lineno))
    return sorted(found)


def wywolania_odsiane():
    """To samo dla `TW.walk` — żeby cisza wyżej znaczyła „idzie przez odsianie",
    a nie „przejść nie ma wcale"."""
    found = []
    for relative in _pliki_python():
        try:
            drzewo = ast.parse(open(os.path.join(ROOT, relative), encoding="utf-8").read())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(drzewo):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "walk"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "TW"):
                found.append((relative.replace(os.sep, "/"), node.lineno))
    return sorted(found)


def _drzewo_probne(baza, pominiety):
    """Dwa pliki: jeden w gałęzi widzianej, drugi w gałęzi `pominiety`."""
    os.makedirs(os.path.join(baza, "widoczne"), exist_ok=True)
    os.makedirs(os.path.join(baza, pominiety, "kopia"), exist_ok=True)
    with open(os.path.join(baza, "widoczne", "a.py"), "w", encoding="utf-8") as u:
        u.write("STALA_WIDZIANA = 1\n")
    with open(os.path.join(baza, pominiety, "kopia", "a.py"), "w", encoding="utf-8") as u:
        u.write("STALA_Z_KOPII = 1\n")


# --------------------------------------------------------------------------- testy


def test_no_tool_walks_the_tree_without_the_shared_filter():
    """Każde `os.walk` w `tools/` idzie przez odsianie — poza samym odsianiem.

    Bramka jest na WOŁANIU, a nie na wyniku, bo wynik zależy od tego, co akurat leży
    na dysku: przejście bez odsiania jest dziś ciche wyłącznie dlatego, że nikt nie
    położył kopii pod `tools/`. Cisza, której warunkiem jest stan katalogu, nie jest
    bramką.
    """
    zle = [(p, w) for p, w in wywolania_os_walk() if p not in WOLNO_WPROST]
    assert zle == [], (
        "przejście po drzewie z pominięciem odsiania z `.gitignore`: %s "
        "— użyj `tree_walk.walk`" % zle)


def test_the_direct_call_list_stays_closed_and_every_entry_is_still_used():
    """Dwa wyjątki, z powodem, i każdy MUSI mieć w swoim pliku wołanie, którego dotyczy.

    Wpis bez wołania jest zdaniem o repozytorium, które przestało być prawdziwe —
    ta sama choroba, co martwa stała z 6.B29. Powód krótszy niż 40 znaków też nie
    przechodzi: „bo tak" jest wpisem, nie uzasadnieniem.
    """
    assert len(WOLNO_WPROST) <= MAX_WOLNO_WPROST, sorted(WOLNO_WPROST)
    wprost = {p for p, _w in wywolania_os_walk()}
    for plik, powod in sorted(WOLNO_WPROST.items()):
        assert plik in wprost, (
            "wyjątek na `%s` nie dotyczy już żadnego wołania — zdejmij go" % plik)
        assert len(powod) >= 40, plik


def test_the_gate_is_looking_at_a_tree_that_still_has_walks_in_it():
    """Kontrola przyrządu: pusta lista wyżej byłaby zielona także przy zepsutym skanie.

    Liczba jest PODŁOGĄ, nie zapadką: wołań może przybyć i to jest normalne. Zejście
    poniżej znaczy, że skan przestał widzieć pliki, a nie że przejść ubyło — tego
    pilnuje osobno lista plików niżej.
    """
    odsiane = wywolania_odsiane()
    assert len(odsiane) >= 14, (
        "skan widzi %d wołań `TW.walk` — wzorzec albo lista plików się rozjechały: %s"
        % (len(odsiane), odsiane))
    pliki = {p for p, _w in odsiane}
    assert "tools/track/data_freshness.py" in pliki, (
        "skan nie widzi `tools/track/`, czyli chodzi po węższym drzewie niż `tools`")
    assert len([p for p in pliki if p.startswith("tools/tests/")]) >= 11, sorted(pliki)


def test_the_ignored_directory_list_is_read_from_gitignore_not_copied():
    """Lista bierze się z `.gitignore`, więc nowy wpis działa bez ruszania kodu."""
    nazwy, sciezki = TW.wzorce_katalogow(
        "# komentarz\n"
        "build/\n"
        "data/gtfs/\n"
        "/tylko-w-korzeniu/\n"
        "*.pyc\n"
        "!nie-pomijaj/\n"
        "plik.txt\n")
    assert nazwy == {"build"}, nazwy
    assert sciezki == {"data/gtfs", "tylko-w-korzeniu"}, sciezki
    # Wpisy plikowe i zaprzeczenia NIE wchodzą: przycięcie gałęzi na `*.pyc` odcięłoby
    # katalog o takiej nazwie, a na `!` — wręcz odwróciłoby znaczenie wpisu.
    assert "*.pyc" not in nazwy and "plik.txt" not in nazwy
    assert "nie-pomijaj" not in nazwy and "nie-pomijaj" not in sciezki


def test_the_real_gitignore_has_no_directory_pattern_with_a_star():
    """Gwiazdki w nazwie katalogu ten moduł NIE zna — i mówi to, zamiast milczeć.

    Wpis w rodzaju `tmp-*/` przeszedłby dziś przez `wzorce_katalogow` jako nazwa
    dosłowna i nie odciąłby niczego. Bramka pilnuje, żeby taki wpis był widoczny
    w tym samym commicie, w którym powstaje.
    """
    nazwy, sciezki = TW.pominiete()
    z_gwiazdka = [w for w in nazwy | sciezki if "*" in w or "?" in w or "[" in w]
    assert z_gwiazdka == [], (
        "`.gitignore` ma katalogowy wzorzec z maską: %s — `tree_walk.wzorce_katalogow` "
        "traktuje go dosłownie i niczego nie odetnie" % z_gwiazdka)


def test_the_filter_skips_a_branch_that_os_walk_enters():
    """Pomiar różnicy na drzewie probnym: `os.walk` wchodzi, `TW.walk` nie.

    Bez tej pary „bramka przeszła" znaczyłoby tylko tyle, że nazwy funkcji się
    zgadzają — a nie że odsianie cokolwiek odsiewa.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as baza:
        _drzewo_probne(baza, "build")
        with open(os.path.join(baza, ".gitignore"), "w", encoding="utf-8") as u:
            u.write("build/\n")
        goly = sorted(n for _b, _d, pliki in os.walk(baza) for n in pliki)
        odsiany = sorted(n for _b, _d, pliki in TW.walk(baza, baza) for n in pliki)
        assert goly == [".gitignore", "a.py", "a.py"], goly
        assert odsiany == [".gitignore", "a.py"], odsiany


def test_a_copy_under_an_ignored_directory_does_not_move_the_dead_constant_scan():
    """Zmierzony przypadek 6.D74 odtworzony na drzewie probnym.

    Pomiar z drzewa projektu (`tools/build/kopia/`, `definicje` **917 → 1511**) jest
    zapisany w raporcie, a nie tutaj: kopia 12 MB w zestawie testów kosztuje sekundy
    i zostawia pliki w drzewie projektu (nauczka z 6.D62, gdzie atrapa sieci zostawiła
    dwa kafle w prawdziwej pamięci). Tutaj stoi ten sam kształt na drzewie w `/tmp`.
    """
    import tempfile
    import test_dead_constants as DC
    with tempfile.TemporaryDirectory() as baza:
        for drzewo in DC.DRZEWA:
            os.makedirs(os.path.join(baza, drzewo), exist_ok=True)
        with open(os.path.join(baza, ".gitignore"), "w", encoding="utf-8") as u:
            u.write("build/\n")
        with open(os.path.join(baza, "tools", "a.py"), "w", encoding="utf-8") as u:
            u.write("STALA_WIDZIANA = 1\n")
        przed = len(DC.definicje(baza))
        os.makedirs(os.path.join(baza, "tools", "build", "kopia"))
        with open(os.path.join(baza, "tools", "build", "kopia", "a.py"),
                  "w", encoding="utf-8") as u:
            u.write("STALA_Z_KOPII = 1\n")
        po = len(DC.definicje(baza))
    assert (przed, po) == (1, 1), (
        "kopia pod katalogiem pominiętym w `.gitignore` zmieniła liczbę skanu: "
        "%d -> %d" % (przed, po))


# 6.D25: uruchomienie tego pliku WPROST idzie tą samą drogą, co cały zestaw —
# z licznikiem asercji i z odmową przy zerze testów.


# --- 6.D97: własna lista katalogów obok wspólnego odsiania ------------------------
#
# Po 6.D74 czternaście przejść poszło przez `TW.walk`, ale w drzewie zostały cztery
# filtry robiące to samo drugi raz. Trzy z nich były DRUGĄ, uboższą kopią listy
# z `.gitignore`: `BUILD_DIRS = {"bin", "obj"}` (`test_readme_claims.py`),
# `"__pycache__" in katalog` (`test_dead_constants.py`) i `os.sep + "obj" in katalog
# or os.sep + "bin" in katalog` (`test_dead_constants_csharp.py`). Dopóki stały obok
# wspólnego odsiania, czytający nie wiedział, która lista rozstrzyga — a przy
# następnym wpisie w `.gitignore` rozjechałyby się po cichu.
#
# Czwarty (`os.sep + "tests" in base` w `mutation_sweep.py`) NIE jest kopią i został:
# tego katalogu `.gitignore` nie zna i znać nie powinien, bo jest śledzony. Odsiewa
# go reguła NARZĘDZIA („mutujemy kod pod testem, nigdy testów"), nie reguła
# repozytorium — i różnica między tymi dwiema regułami jest treścią tej bramki.

#: JAWNE, ZAMKNIĘTE wyjątki: `(plik, nazwa katalogu, powód)` dla filtrów, które
#: odsiewają katalog Z WŁASNEGO powodu, nie dlatego, że stoi w `.gitignore`.
#: Pusto, i to jest wynik pomiaru: jedyny taki filtr w drzewie odsiewa `tests`,
#: a `tests` w `.gitignore` NIE STOI, więc bramka go nie widzi i nie musi.
FILTRY_Z_WLASNEGO_POWODU = {
    ("tools/tests/test_sim_untested_members.py", "obj"): (
        '`_is_generated` NIE odsiewa katalogu z przejścia — klasyfikuje ścieżki '
        'z `glob.glob`, żeby moduł mógł policzyć stan PRZED (z plikami generowanymi) '
        'i PO (bez nich). Zdjęcie tego filtru zabrałoby pomiar, nie duplikat'),
    ("tools/tests/test_sim_untested_members.py", "bin"): (
        "druga połowa tego samego warunku, ten sam powód"),
}


def filtry_katalogow_z_gitignore():
    """`[(plik, wiersz, nazwa)]` — miejsca odsiewające katalog, który jest w `.gitignore`.

    Szukane w drzewie składni, w plikach, które w ogóle chodzą po drzewie: literał
    napisowy równy nazwie katalogu z `.gitignore`, użyty w warunku albo w zbiorze.
    Grep po nazwie łapałby też komentarze i docstringi — a w tym module stoi ich
    kilkanaście, bo cała ta sekcja jest O tych nazwach.
    """
    nazwy, _sciezki = TW.pominiete()
    chodzace = {plik for plik, _wiersz in wywolania_odsiane() + wywolania_os_walk()}
    znalezione = []
    for relative in sorted(chodzace):
        try:
            zrodlo = open(os.path.join(ROOT, relative), encoding="utf-8").read()
            drzewo = ast.parse(zrodlo)
        except (OSError, SyntaxError):
            continue
        # Wnętrza funkcji `test_*` są POMIJANE i to jest poprawka z pomiaru: pierwsza
        # wersja skanu zgłosiła `build` z wejścia syntetycznego w
        # `test_the_ignored_directory_list_is_read_from_gitignore_not_copied` — czyli
        # napis, który jest DANYMI testu parsera, a nie filtrem. Filtry mieszkają
        # w pomocnikach i na poziomie modułu, fixture w testach.
        wnetrza = set()
        for funkcja in ast.walk(drzewo):
            if (isinstance(funkcja, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and funkcja.name.startswith("test_")):
                for pod in ast.walk(funkcja):
                    wnetrza.add(id(pod))
        for node in ast.walk(drzewo):
            if not isinstance(node, (ast.If, ast.Set, ast.ListComp, ast.Compare)):
                continue
            for pod in ast.walk(node):
                if id(pod) in wnetrza:
                    continue
                if (isinstance(pod, ast.Constant) and isinstance(pod.value, str)
                        and pod.value in nazwy):
                    znalezione.append((relative, pod.lineno, pod.value))
    return sorted(set(znalezione))


def test_zaden_skan_nie_trzyma_wlasnej_kopii_listy_z_gitignore():
    """Druga lista tych samych katalogów rozjeżdża się przy pierwszym nowym wpisie."""
    znalezione = [w for w in filtry_katalogow_z_gitignore()
                  if (w[0], w[2]) not in FILTRY_Z_WLASNEGO_POWODU]
    assert not znalezione, (
        "skan chodzący po drzewie odsiewa katalog, który JUŻ odsiewa `TW.walk` "
        "z `.gitignore` — dwie listy tej samej rzeczy rozjadą się przy następnym "
        f"wpisie: {znalezione}")


def test_lista_wyjatkow_filtrow_nie_gnije():
    """Wyjątek bez pokrycia w drzewie ma zniknąć z listy.

    Asercja o PUSTOŚCI stoi tu, bo pusta pętla nie wykonuje żadnej i test byłby
    cichym pominięciem. Dziś lista jest pusta i to jest zmierzony stan.
    """
    obecne = {(w[0], w[2]) for w in filtry_katalogow_z_gitignore()}
    if not FILTRY_Z_WLASNEGO_POWODU:
        assert obecne == set(), sorted(obecne)
        return
    for klucz, powod in sorted(FILTRY_Z_WLASNEGO_POWODU.items()):
        assert klucz in obecne, f"{klucz} nie ma już filtru — zdejmij wpis ({powod})"


def test_skan_filtrow_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola PRZYRZĄDU: cisza ma znaczyć „czysto", a nie „skan ślepy".

    Bramka wyżej jest dziś zielona, więc bez tego testu nie dałoby się odróżnić
    drzewa bez kopii od skanu, który przestał czegokolwiek szukać. Sprawdzane jest
    to, na czym skan stoi: że nazwy katalogów bierze z `.gitignore` (a nie z listy
    wpisanej tutaj) i że `tests` — jedyny filtr, który został — do tego zbioru
    NIE należy, więc jego obecność w drzewie bramki nie zapala.
    """
    nazwy, _sciezki = TW.pominiete()
    for oczekiwana in ("bin", "obj", "__pycache__", "build", "renders", ".venv"):
        assert oczekiwana in nazwy, (
            f"{oczekiwana!r} zniknęło z listy katalogów czytanej z `.gitignore` — "
            "bramka wyżej przestała widzieć kopię akurat tego katalogu")
    assert "tests" not in nazwy, (
        "`tests` trafiło do listy z `.gitignore`; filtr w `mutation_sweep.py` "
        "zapaliłby wtedy bramkę, choć odsiewa katalog z własnego powodu")
    assert len(nazwy) >= 10, (
        f"lista z `.gitignore` skurczyła się do {len(nazwy)} nazw — skan miałby "
        "wtedy czego nie szukać")

if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
