"""Granica `\\b` postawiona przy cyfrze — ile jej jest i ile dzis ROZCINA liczbe.

**Skad ta bramka.** 6.D275 naprawilo jedna granice w `SMIECI_W_PROZIE`, bo wzorzec
`\\b\\d+\\s*/\\s*\\d+\\b` wycinal `090 / 0` ze srodka ciagu `0,090 / 0,087 / 0,085 s`
i zostawial dwa urwane czlony, z ktorych kazdy czytal sie jak liczba. Tym samym sitem
wyszly zaraz potem dwa kolejne ksztalty, wiec nie byl to wypadek, tylko WZORZEC.
`\\b` nie jest granica liczby: przecinek i kropka sa dla niego granica slowa,
a w tym repozytorium ulamek zapisuje sie PRZECINKIEM.

Ta bramka nie przepisuje wzorcow — to byla decyzja o zachowaniu kazdej bramki,
ktora ich uzywa, i 6.D277 ma ja poza zakresem. Bramka PRZYBIJA populacje, zeby
kolejna taka granica nie weszla do drzewa niezauwazona.
"""

import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Token liczbowy w prozie tego repozytorium: czesc calkowita i ulamek po PRZECINKU
#: albo kropce. Rozciecie liczby poznaje sie po tym, ze granica trafienia wypada
#: SCISLE WEWNATRZ takiego tokenu — granica rowna jego krawedzi rozcieciem nie jest,
#: bo po poprawnie dopasowanej dacie tez stoi przecinek, tyle ze zdaniowy.
TOKEN_LICZBOWY = re.compile(r"\d+(?:[.,]\d+)*")

#: Kwantyfikatory, ktore trzeba przeskoczyc, zeby zobaczyc, przy CZYM stoi `\b`.
#: Bez tego `\d+\b` czyta sie jako granica przy `+`, a nie przy cyfrze — i wlasnie
#: ten ksztalt mial wzorzec, ktory pozycje wywolal.
KWANTYFIKATOR = set("+*?")
CYFRY = set("0123456789")

#: Populacja, na ktorej stoi przybicie nizej. PODLOGA, bo skaner oslepiony do zera
#: przechodzi kazde przybicie celujaco (6.D27) — przybita lista bylaby wtedy pusta
#: po obu stronach i zgadzalaby sie sama ze soba.
MIN_LITERALOW_SKANOWANYCH = 170

#: Zapadka gorna na ROZCIECIA ZYWE. Wolno ja wylacznie OBNIZAC: kazde rozciecie,
#: ktore znika z drzewa, ma ja obnizyc, a kazde nowe ma zapalic bramke.
MAX_ROZCIEC_ZYWYCH = 1


def _tokeny(wzorzec):
    """Tokeny wzorca: (rodzaj, tekst), rodzaj w {esc, klasa, kwant, zwykly}."""
    out, i, n = [], 0, len(wzorzec)
    while i < n:
        znak = wzorzec[i]
        if znak == "\\" and i + 1 < n:
            out.append(("esc", wzorzec[i:i + 2]))
            i += 2
        elif znak == "[":
            j = i + 1
            if j < n and wzorzec[j] == "^":
                j += 1
            if j < n and wzorzec[j] == "]":
                j += 1
            while j < n:
                if wzorzec[j] == "\\":
                    j += 2
                    continue
                if wzorzec[j] == "]":
                    j += 1
                    break
                j += 1
            out.append(("klasa", wzorzec[i:j]))
            i = j
        elif znak == "{":
            j = wzorzec.find("}", i)
            if j == -1:
                out.append(("zwykly", znak))
                i += 1
            else:
                out.append(("kwant", wzorzec[i:j + 1]))
                i = j + 1
        elif znak in KWANTYFIKATOR:
            out.append(("kwant", znak))
            i += 1
        else:
            out.append(("zwykly", znak))
            i += 1
    return out


def _dopasowuje_cyfre(token):
    rodzaj, tekst = token
    if rodzaj == "esc":
        return tekst == "\\d"
    if rodzaj == "klasa":
        tresc = tekst[1:-1]
        if tresc.startswith("^"):
            return False
        return "\\d" in tresc or "0-9" in tresc or any(z in CYFRY for z in tresc)
    if rodzaj == "zwykly":
        return tekst in CYFRY
    return False


def granice_przy_cyfrze(wzorzec):
    """Opisy `\\b` stojacych bezposrednio przy cyfrze albo `\\d` — po obu stronach."""
    toks = _tokeny(wzorzec)
    out = []
    for k, tok in enumerate(toks):
        if tok != ("esc", "\\b"):
            continue
        if k + 1 < len(toks) and _dopasowuje_cyfre(toks[k + 1]):
            out.append("\\b PRZED %s" % toks[k + 1][1])
        j = k - 1
        while j >= 0 and toks[j][0] == "kwant":
            j -= 1
        if j >= 0 and _dopasowuje_cyfre(toks[j]):
            out.append("\\b PO %s" % toks[j][1])
    return out


def _nazwa_wywolania(fn):
    if isinstance(fn, ast.Attribute):
        return fn.attr if isinstance(fn.value, ast.Name) and fn.value.id == "re" else None
    if isinstance(fn, ast.Name):
        return fn.id
    return None


def literaly_wzorcow(root):
    """(czytelne, nieczytelne) literaly pierwszego argumentu `re.compile` pod `tools/`.

    `root` jest tu argumentem JAWNYM, a nie domyslnym wiazanym przy imporcie:
    domyslny wiaze sie raz i podmiana `modul.ROOT` jest wtedy no-opem, co daje
    cztery identyczne odczyty czytajace sie jak wynik (6.D265, 6.D269).
    """
    czytelne, nieczytelne, widziane = [], [], set()
    # `TW.walk`, a nie `os.walk`: odsianie idzie z `.gitignore`, a wlasna kopia
    # tej listy rozjechalaby sie przy nastepnym wpisie (druga lista tej samej rzeczy).
    for baza, _katalogi, pliki in TW.walk(os.path.join(root, "tools"), root):
        for nazwa in sorted(pliki):
            if not nazwa.endswith(".py"):
                continue
            pelna = os.path.join(baza, nazwa)
            rel = os.path.relpath(pelna, root)
            with open(pelna, encoding="utf-8") as uchwyt:
                try:
                    drzewo = ast.parse(uchwyt.read())
                except SyntaxError:
                    continue
            for wezel in ast.walk(drzewo):
                if not isinstance(wezel, ast.Call):
                    continue
                if _nazwa_wywolania(wezel.func) != "compile" or not wezel.args:
                    continue
                # Deduplikacja po (plik, wiersz, kolumna): `ast.walk` po module
                # odwiedza wezel funkcji zagniezdzonej RAZ, ale ta sama ochrona
                # kosztuje nic, a bez niej licznik potrafi liczyc dwa razy.
                klucz = (rel, wezel.lineno, wezel.col_offset)
                if klucz in widziane:
                    continue
                widziane.add(klucz)
                arg = wezel.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    czytelne.append((rel, arg.value))
                else:
                    nieczytelne.append((rel, wezel.lineno, type(arg).__name__))
    return czytelne, nieczytelne


def wzorce_z_granica_przy_cyfrze(root):
    """Klucz `(plik, wzorzec)` dla kazdego literalu z `\\b` przy cyfrze.

    Kluczem jest WZORZEC, a nie numer wiersza: kotwica na numerze rozjezdza sie
    przy nastepnej wlasnej edycji pliku (6.D229).
    """
    czytelne, _ = literaly_wzorcow(root)
    return {(rel, wz) for rel, wz in czytelne if granice_przy_cyfrze(wz)}


def rozciecia_liczby(wzorzec, tekst):
    """(trafienie, rozciety token) dla kazdej granicy wypadajacej WEWNATRZ liczby."""
    out = []
    for m in wzorzec.finditer(tekst):
        for tok in TOKEN_LICZBOWY.finditer(tekst):
            if tok.start() < m.start() < tok.end() or tok.start() < m.end() < tok.end():
                out.append((m.group(0), tok.group(0)))
                break
    return out


#: Plik tej bramki — odejmowany od liczby naglowkowej, a NIE od skanu.
#: Dwa wzorce nizej to atrapy kontroli przyrzadu stojace w tym wlasnie module:
#: skan znajduje je slusznie, bo naprawde maja `\b` przy cyfrze, ale wliczenie ich
#: do liczby, ktora pozycja mierzy, byloby mierzeniem WLASNEGO PRZYRZADU. Sa wiec
#: w zbiorze przybitym (zeby nie mogly zniknac cicho) i poza liczba naglowkowa.
TA_BRAMKA = "tools/tests/test_digit_boundaries.py"

#: Liczby, ktorych zadalo pole „Wyjscie" 6.D277 — z drzewa, nie wpisane z reki.
#: Zmierzone 18.09.2026 na `3ed9cc0`, przed dolozeniem tego modulu.
WZORCOW_POZA_TA_BRAMKA = 7
PLIKOW_POZA_TA_BRAMKA = 5

#: Komplet literalow, ktore dzis stawiaja `\b` przy cyfrze. Zbior PRZYBITY i
#: porownywany W OBIE STRONY, bo jest ich kilka — lista tej dlugosci jeszcze jest
#: lista, a nie podpisem pod obrazkiem (6.D243). Klucz to `(plik, wzorzec)`.
GRANICE_PRZY_CYFRZE = {
    # --- atrapy kontroli przyrzadu TEGO modulu, poza liczba naglowkowa ---
    (TA_BRAMKA, r"\b\d+\s*/\s*\d+\b"),
    (TA_BRAMKA, r"\b\d{2}\.\d{2}\.\d{4}\b"),
    # --- siedem wzorcow zmierzonych w drzewie, w pieciu plikach ---
    ("tools/tests/test_backlog.py",
     r"\b\d{2}\.\d{2}\.\d{4}\b"),
    ("tools/tests/test_message_claims.py",
     r"\b6\.[A-Z]\d+\b"),
    ("tools/tests/test_message_claims.py",
     r"\bMB-\d+\b"),
    ("tools/tests/test_report_claims.py",
     r"\b\d{2}\.\d{2}\.\d{4}\b"
     r"|\b6\.D\d+\b|\bMB-\d+\b|\bKN-\d+[a-z]?\b"
     r"|#\d+\b|§\s?\d+(?:\.\d+)*"
     r"|[\w./-]+\.(?:cs|py|md|json|yml|glb|sh|txt|csproj)(?::\d+(?:-\d+)?)?"
     r"|\b[0-9a-f]{7,40}\b|\bwiersz\w*\s+\d+\b"),
    ("tools/tests/test_report_hygiene.py",
     r"\b20\d\d-\d\d-\d\d\b"),
    ("tools/tests/test_report_hygiene.py",
     r"\b\d\d\.\d\d\.20\d\d\b"),
    ("tools/tests/test_suite_runtime_budget.py",
     r"\b\d{1,2}\.\d{2}\.\d{4}\b"),
}


def test_komplet_granic_przy_cyfrze_zgadza_sie_z_drzewem():
    """**Zbior przybity, porownywany w obie strony — inaczej nowa granica wchodzi cicho.**

    Podloga na populacje skanowana stoi obok przybicia i jest jego warunkiem:
    skaner, ktory oslepl, zwraca zbior pusty i zgadza sie sam ze soba.
    """
    czytelne, _ = literaly_wzorcow(ROOT)
    assert len(czytelne) >= MIN_LITERALOW_SKANOWANYCH, (
        "literalow `re.compile` przeskanowano %d przy podlodze %d — skaner oslepl, "
        "a oslepiony przechodzi przybicie nizej celujaco (6.D27)"
        % (len(czytelne), MIN_LITERALOW_SKANOWANYCH))

    zmierzone = wzorce_z_granica_przy_cyfrze(ROOT)
    doszly = sorted(zmierzone - GRANICE_PRZY_CYFRZE)
    znikly = sorted(GRANICE_PRZY_CYFRZE - zmierzone)
    assert not doszly, (
        "nowa granica `\\b` przy cyfrze weszla do drzewa i nikt jej nie widzial — "
        "`\\b` nie jest granica liczby, bo przecinek jest dla niego granica slowa: %s"
        % doszly)
    assert not znikly, (
        "granica z przybitego zbioru zniknela z drzewa — jesli to naprawa, zdejmij "
        "ja z `GRANICE_PRZY_CYFRZE` w tym samym commicie: %s" % znikly)


def test_czytnik_odroznia_granice_przy_CYFRZE_od_granicy_przy_LITERZE():
    """**Kontrola przyrzadu: sito ma odsiac `\\b` stojace przy literze.**

    Oba ksztalty stoja w zywym drzewie obok siebie — `\\bkod\\s+\\d+` ma granice przy
    literze `k`, a `\\bMB-\\d+\\b` ma jedna przy literze i jedna za `\\d+`. Sito, ktore
    nie umie ich rozdzielic, zglasza kazdy wzorzec i liczba przestaje cokolwiek znaczyc.
    """
    assert granice_przy_cyfrze(r"\b\d+\s*/\s*\d+\b"), (
        "sito nie widzi wzorca, ktory pozycje WYWOLAL")
    assert granice_przy_cyfrze(r"\bMB-\d+\b") == ["\\b PO \\d"], (
        "granica za `\\d+` ma sie liczyc, a granica przed litera `M` nie: %s"
        % granice_przy_cyfrze(r"\bMB-\d+\b"))
    assert not granice_przy_cyfrze(r"\bkod\s+\d+(?![\d,.])"), (
        "`\\b` przy literze `k` trafilo na liste — sito liczy pisownie, nie ksztalt")
    assert not granice_przy_cyfrze(r"\bslowo\b"), (
        "wzorzec bez ani jednej cyfry trafil na liste")


def test_kryterium_rozciecia_zna_przypadek_ktory_pozycje_wywolal():
    """**Kontrola przyrzadu na kryterium, a nie na populacji.**

    Kryterium sprawdzane jest na tej samej parze, ktora 6.D275 naprawilo: stary
    wzorzec ma rozcinac, naprawiony ma nie rozcinac NICZEGO. Obok stoi ksztalt
    odwrotny — poprawnie dopasowana data, po ktorej przecinek jest zdaniowy,
    a nie czescia liczby; bez tej drugiej polowy kryterium zglasza kazda date.
    """
    przypadek = "srednia to 0,090 / 0,087 / 0,085 s na modul"
    stary = re.compile(r"\b\d+\s*/\s*\d+\b")
    naprawiony = re.compile(r"(?<![\d,.])\d+\s*/\s*\d+(?![\d,.])")
    assert rozciecia_liczby(stary, przypadek), (
        "kryterium nie widzi rozciecia, ktore pozycje wywolalo")
    assert not rozciecia_liczby(naprawiony, przypadek), (
        "kryterium zglasza wzorzec JUZ NAPRAWIONY — mierzy pisownie, nie skutek")
    data = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")
    assert not rozciecia_liczby(data, "DECYZJA z 04.09.2026, pozycje 3 i 4"), (
        "przecinek zdaniowy po poprawnej dacie uznany za rozciecie — kryterium "
        "dawaloby wtedy falszywe trafienia na kazdej dacie w drzewie")


def test_ile_wzorcow_stawia_granice_przy_cyfrze_i_w_ilu_plikach():
    """**Dwie z trzech liczb, ktorych zadalo pole „Wyjscie" — liczone z drzewa.**

    Atrapy tego modulu sa odejmowane, bo inaczej liczba mowilaby o przyrzadzie,
    a nie o drzewie. Odejmowanie jest tu WIDOCZNE i przybite: gdyby atrap ubylo
    albo przybylo, zapali sie test wyzej, a nie ten.
    """
    zmierzone = wzorce_z_granica_przy_cyfrze(ROOT)
    obce = {(plik, wz) for plik, wz in zmierzone if plik != TA_BRAMKA}
    pliki = {plik for plik, _ in obce}
    assert len(obce) == WZORCOW_POZA_TA_BRAMKA, (
        "wzorcow z `\\b` przy cyfrze poza ta bramka jest %d, a przybite %d: %s"
        % (len(obce), WZORCOW_POZA_TA_BRAMKA, sorted(obce)))
    assert len(pliki) == PLIKOW_POZA_TA_BRAMKA, (
        "plikow jest %d, a przybite %d: %s"
        % (len(pliki), PLIKOW_POZA_TA_BRAMKA, sorted(pliki)))


#: Podloga na korpus, na ktorym mierzy sie rozciecia zywe. Ten sam powod co wyzej:
#: korpus pusty daje zero rozciec i przechodzi zapadke gorna celujaco (6.D27).
MIN_TEKSTOW_W_KORPUSIE = 800

#: Jedyne ROZCIECIE ZYWE w drzewie, przybite co do adresu i co do tokenu.
#: `\b[0-9a-f]{7,40}\b` z `ADRES_NIE_TWIERDZENIE` mial lapac skrot commita, a lapie
#: siedmiocyfrowa CZESC CALKOWITA liczby dziesietnej, bo `5400088` sklada sie z samych
#: znakow legalnych w zapisie szesnastkowym, a przecinek jest dla `\b` granica slowa.
#: Przepisanie tego wzorca jest poza zakresem 6.D277 — kazdy z siedmiu jest osobna
#: zmiana zachowania bramki, ktora go uzywa. Tu jest PRZYBITY, a nie naprawiony.
ROZCIECIA_ZYWE = {("tools/tests/test_report_claims.py", "5400088", "5400088,438")}


def _wzorce_tnace():
    """Pieciu wzorcow uzywanych przez `sub`, razem z ich prawdziwym korpusem.

    Tylko `sub` zostawia urwany czlon w tekscie, ktory czyta potem ktos dalej;
    `search` i `findall` daja falszywe trafienie, ale nowej „liczby" nie tworza.
    Dwa wzorce szukajace (`DATA_DECYZJI`, `_DATA_PL`) sa wiec poza tym testem
    — i jest to zwezenie ZAPISANE, a nie przemilczane.

    Korpus prozy brany jest SUROWY, przed zdjeciem pogrubien i wczesniejszych
    smieci. To nadzbior tego, co wzorzec dostaje w bramce — dla zapadki gornej
    strona bezpieczna, bo rozciecie mozna tu zobaczyc, a przegapic nie.
    """
    import test_message_claims as TMC
    import test_report_claims as TRC
    import test_report_hygiene as TRH

    proza_tools = []
    for nazwa, wiersz, tekst, _rodzaj, _od, _do in TMC.proza(None, ROOT):
        proza_tools.append(("%s:%d" % (nazwa, wiersz), tekst))
    punkty = []
    for nazwa, naglowek, tresc in TRC.sekcje_zauwazone():
        for punkt in TRC.punkty_sekcji(tresc):
            punkty.append((nazwa, punkt))
    naglowki = [(nazwa, TRH._header(tekst)) for nazwa, tekst in TRH._reports()]

    # Indeks 4 jest tu TRESCIA, a nie kompletnoscia: to wlasnie ten wzorzec
    # 6.D275 naprawilo, i pierwsza wersja tego testu go NIE MIALA. Kontrola
    # negatywna wyszla wtedy na dwie czerwienie zamiast trzech, i to ona
    # pokazala, ze bramka jest slepa na przypadek, ktory pozycje wywolal.
    return [
        ("tools/tests/test_message_claims.py", TMC.SMIECI_W_PROZIE[1], proza_tools),
        ("tools/tests/test_message_claims.py", TMC.SMIECI_W_PROZIE[2], proza_tools),
        ("tools/tests/test_message_claims.py", TMC.SMIECI_W_PROZIE[4], proza_tools),
        ("tools/tests/test_report_claims.py", TRC.ADRES_NIE_TWIERDZENIE, punkty),
        ("tools/tests/test_report_hygiene.py",
         TRH.NOTATIONS["ISO (2026-09-02)"], naglowki),
        ("tools/tests/test_report_hygiene.py",
         TRH.NOTATIONS["PL (02.09.2026)"], naglowki),
    ]


def test_ile_wzorcow_rozcina_dzis_liczbe_na_zywym_drzewie():
    """**Trzecia liczba z pola „Wyjscie" — i jest niezerowa.**

    Zapadka gorna z przybitym adresem: wolno ja tylko OBNIZAC. Nowe rozciecie
    zapala bramke z nazwa pliku i rozcietym tokenem, a nie sama liczba.
    """
    wzorce = _wzorce_tnace()
    razem_tekstow = sum(len(korpus) for _, _, korpus in wzorce)
    assert razem_tekstow >= MIN_TEKSTOW_W_KORPUSIE, (
        "korpus ma %d tekstow przy podlodze %d — czytnik oslepl, a oslepiony daje "
        "zero rozciec i przechodzi zapadke ponizej celujaco (6.D27)"
        % (razem_tekstow, MIN_TEKSTOW_W_KORPUSIE))

    zmierzone = set()
    for plik, wzorzec, korpus in wzorce:
        for _etykieta, tekst in korpus:
            for trafienie, token in rozciecia_liczby(wzorzec, tekst):
                zmierzone.add((plik, trafienie, token))

    assert len(zmierzone) <= MAX_ROZCIEC_ZYWYCH, (
        "wzorcow rozcinajacych liczbe na zywym drzewie jest %d przy zapadce %d — "
        "zapadke wolno tylko OBNIZAC: %s"
        % (len(zmierzone), MAX_ROZCIEC_ZYWYCH, sorted(zmierzone)))
    doszly = sorted(zmierzone - ROZCIECIA_ZYWE)
    znikly = sorted(ROZCIECIA_ZYWE - zmierzone)
    assert not doszly, "nowe rozciecie liczby w drzewie: %s" % doszly
    assert not znikly, (
        "rozciecie z przybitego zbioru zniknelo — jesli to naprawa, obniz "
        "`MAX_ROZCIEC_ZYWYCH` i zdejmij wpis w tym samym commicie: %s" % znikly)


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
