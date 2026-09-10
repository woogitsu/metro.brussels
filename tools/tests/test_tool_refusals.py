#!/usr/bin/env python3
"""Narzędzie odmawia przez `raise`, nie przez `assert` — bo `-O` zdejmuje `assert`.

**Skąd ta bramka (6.D94).** Zmierzone 09.09.2026 przy 6.D71, potwierdzone 10.09.2026
przed poprawką: `python3 -O tools/tests/test_all.py` kończył **kodem 1** wobec 0 przy
przebiegu zwykłym, przy tej samej liczbie testów (2178) i modułów (116). Padały
dokładnie dwa, oba pilnujące ODMOWY narzędzia:

    FAIL test_platform_exactly_as_wide_as_the_chamber_is_refused:
         peron zerowej szerokości przeszedł po prawej stronie
    FAIL test_platform_exactly_as_wide_as_the_chamber_is_refused_on_the_left_side_too:
         peron zerowej szerokości przeszedł po lewej stronie

`-O` zdejmuje `assert` w **każdym** module, nie tylko w testowym, więc pod `-O` peron
zerowej szerokości przechodził i geometria powstawała. To nie była usterka testów.

**Ile ich było, policzone z drzewa składni, nie grepem po napisie: TRZY**, w dwóch
plikach, i wszystkie trzy były strażnikami, żaden niezmiennikiem wewnętrznym:

    tools/blender/station_sections.py:97,100  slab_sections  outer > inner / outer < inner
    tools/physics/braking.py:65               params.design  rec['status'] == 'design_model'

Pierwsza wersja skanu meldowała **cztery**, bo `assert` z `braking.py` siedzi
w funkcji zagnieżdżonej i wpadał do wyniku dwa razy — raz jako należący do `params`,
raz do `design`. Liczba miejsc jest treścią pola „Wyjście" tej pozycji, więc podwójne
liczenie nie było kosmetyką; skan schodzi teraz rekurencyjnie z pamięcią funkcji.

Drugi z nich jest cichszy i groźniejszy: to kontrola POCHODZENIA liczby, więc pod `-O`
parametr o dowolnym innym statusie wchodził do modelu hamowania bez śladu.

**Kształt odmowy wybrany POMIAREM, nie gustem.** `ValueError` stoi w `tools/` poza
testami **68 razy** jako odmowa narzędzia, a `AssertionError` **nie łapie tam nikt** —
poza `tools/tests/`, gdzie łapały go dwa testy tej właśnie odmowy (poprawione) i trzy
miejsca łapiące własne asercje testu, których ta zmiana nie dotyczy.

**Czego ta bramka NIE zabrania:** `assert` w `tools/tests/`. Tam jest mechanizmem
werdyktu, a nie strażnikiem wejścia, i zestaw nigdy nie chodzi pod `-O` (`test_all.py`
nie ustawia tej flagi, a pole „Poza zakresem" pozycji wyklucza wołanie go tak w CI).
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tree_walk as TW  # noqa: E402

ROOT = TW.ROOT
NARZEDZIA = os.path.join(ROOT, "tools")

#: JAWNA, ZAMKNIĘTA lista `assert`ów, którym wolno zostać w narzędziu, jako
#: `(ścieżka, wiersz, powód)`. **Pusta, i to jest wynik pomiaru, a nie założenie:**
#: wszystkie cztery znalezione były strażnikami i wszystkie cztery zostały zamienione.
#: Pierwszy wyjątek wchodzi tu z powodem i zostaje objęty testem „nie gnije", tak samo
#: jak `WOLNO_WPROST` w `test_tree_walks.py`.
WOLNO_ASSERT = {}


def _moduly():
    for base, _dirs, files in TW.walk(NARZEDZIA):
        if os.sep + "tests" in base:
            continue
        for nazwa in sorted(files):
            if nazwa.endswith(".py"):
                yield os.path.join(base, nazwa)


def asserty(zrodlo, sciezka=""):
    """`[(ścieżka, wiersz, funkcja, treść warunku)]` dla jednego modułu.

    **Zejście jest rekurencyjne z pamięcią funkcji, a nie `ast.walk` po funkcjach,
    i to jest poprawka z pomiaru.** Pierwsza wersja chodziła `ast.walk`iem po każdej
    funkcji osobno, więc `assert` w funkcji ZAGNIEŻDŻONEJ trafiał do wyniku DWA RAZY:
    raz jako należący do funkcji zewnętrznej, raz do wewnętrznej. Na tym repozytorium
    dawało to **cztery** trafienia tam, gdzie `assert`ów jest **trzy** — bo ten
    z `braking.py` siedzi w `design` wewnątrz `params`. Liczba miejsc jest treścią
    pola „Wyjście" pozycji 6.D94, więc podwójne liczenie nie było kosmetyką.
    """
    znalezione = []

    def zejdz(wezel, funkcja):
        for dziecko in ast.iter_child_nodes(wezel):
            if isinstance(dziecko, ast.Assert):
                znalezione.append((sciezka, dziecko.lineno, funkcja,
                                   ast.unparse(dziecko.test)[:80]))
            if isinstance(dziecko, (ast.FunctionDef, ast.AsyncFunctionDef)):
                zejdz(dziecko, dziecko.name)
            else:
                zejdz(dziecko, funkcja)

    zejdz(ast.parse(zrodlo), "<modul>")
    return sorted(znalezione, key=lambda w: (w[0], w[1], w[2]))


def wszystkie_asserty():
    znalezione = []
    for sciezka in _moduly():
        with open(sciezka, encoding="utf-8") as uchwyt:
            znalezione += asserty(uchwyt.read(), os.path.relpath(sciezka, ROOT))
    return znalezione


def test_zadne_narzedzie_nie_broni_warunku_golym_assertem():
    """`-O` zdejmuje `assert`, więc strażnik napisany tak nie jest strażnikiem."""
    znalezione = [w for w in wszystkie_asserty()
                  if (w[0], w[1]) not in WOLNO_ASSERT]
    assert not znalezione, (
        "narzędzie broni warunku gołym `assert`, a `python3 -O` zdejmuje `assert` "
        "w każdym module — pod `-O` ta odmowa znika i wejście przechodzi; zamień na "
        f"`raise ValueError` z powodem: {znalezione}")


def test_lista_wyjatkow_nie_gnije():
    """Wyjątek, którego już nie ma w drzewie, ma zniknąć z listy.

    Asercja o PUSTOŚCI stoi tu, bo pusta pętla nie wykonuje żadnej i test byłby
    cichym pominięciem — bramka asercji tego repozytorium słusznie by go zgłosiła.
    Dziś lista jest pusta i to jest zmierzony stan, a nie brak roboty.
    """
    obecne = {(w[0], w[1]) for w in wszystkie_asserty()}
    if not WOLNO_ASSERT:
        assert obecne == set(), (
            "lista wyjątków jest pusta, a w narzędziach stoją `assert`y — jedno "
            f"z dwojga jest nieaktualne: {sorted(obecne)}")
        return
    for klucz, powod in sorted(WOLNO_ASSERT.items()):
        assert klucz in obecne, (
            f"{klucz} nie ma już `assert`a — zdejmij wpis z WOLNO_ASSERT ({powod})")


def test_skan_widzi_asserty_ktore_ma_widziec():
    """Kontrola PRZYRZĄDU: pusty wynik ma znaczyć „czysto", a nie „skan ślepy".

    Cztery wejścia syntetyczne, każde z innym trybem cichej awarii: `assert` w funkcji,
    `assert` na poziomie modułu, `assert` w zagnieżdżonej funkcji (tam siedział ten
    z `braking.py`) i moduł bez ani jednego — ostatni po to, żeby skan zgłaszający
    wszystko nie przeszedł tego testu.
    """
    w_funkcji = asserty("def f(a):\n    assert a > 0, a\n    return a\n", "x.py")
    assert len(w_funkcji) == 1 and w_funkcji[0][2] == "f", w_funkcji

    w_module = asserty("import os\nassert os.sep == '/'\n", "x.py")
    assert len(w_module) == 1 and w_module[0][2] == "<modul>", w_module

    zagniezdzony = asserty(
        "def zewn(d):\n"
        "    def wewn(k):\n"
        "        assert d[k] == 1, k\n"
        "        return d[k]\n"
        "    return wewn\n", "x.py")
    assert len(zagniezdzony) == 1, (
        "skan nie widzi `assert`a w funkcji zagnieżdżonej — a dokładnie tam stał ten "
        f"z `braking.py`: {zagniezdzony}")
    assert zagniezdzony[0][2] == "wewn", zagniezdzony

    bez = asserty("def f(a):\n    if a <= 0:\n        raise ValueError(a)\n    return a\n", "x.py")
    assert bez == [], f"skan zgłasza odmowę przez `raise` jako `assert`: {bez}"


def test_odmowa_geometryczna_i_pochodzeniowa_dzialaja_takze_pod_O():
    """Obie zamienione odmowy wykonane WPROST, bez pośrednictwa flagi interpretera.

    Test nie uruchamia `-O` (to robi pole „Weryfikacja" pozycji na całym zestawie),
    tylko sprawdza, że odmowa jest zwykłym `raise` — czyli czymś, czego `-O` nie ma
    jak zdjąć. Dwie różne odmowy, bo są to dwie różne klasy kontroli: geometria
    wejścia i pochodzenie liczby.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
    sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))
    import station_sections as SS  # noqa: E402
    import braking as B  # noqa: E402

    try:
        SS.slab_sections(0.5, 0.5, SS.DESIGN_WALL_SETBACK_M, 3.0, -1.0, 1.0)
    except ValueError as e:
        assert "niedodatniej szerokości" in str(e), str(e)
    else:
        raise AssertionError("peron zerowej szerokości przeszedł")

    # Rejestr ODDAJĄCY KAŻDY KLUCZ, o który go poproszą. Dwie wersje wcześniejsze
    # wypisywały klucze z ręki i obie były niepełne — druga wywróciła się na
    # `empty_mass_kg`, czytanym w `params` z pominięciem `design()`. Test czerwony
    # od `KeyError` jest czerwony z niewłaściwego powodu i nie mierzy odmowy;
    # rejestr samouzupełniający się nie może się z tą funkcją rozjechać.
    class _Rejestr(dict):
        def __missing__(self, klucz):
            self[klucz] = {"status": "design_model", "value": 1.0}
            return self[klucz]

    rejestr = {"reference_model": _Rejestr(), "parameters": _Rejestr()}
    assert B.params(rejestr), (
        "komplet z poprawnym statusem ma przejść — inaczej odmowa niżej nic nie mierzy")

    rejestr["reference_model"]["adhesion_wet"]["status"] = "spec"
    try:
        B.params(rejestr)
    except ValueError as e:
        assert "design_model" in str(e) and "adhesion_wet" in str(e), str(e)
    else:
        raise AssertionError(
            "parametr o statusie 'spec' wszedł do modelu hamowania — kontrola "
            "pochodzenia liczby nie zadziałała")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
