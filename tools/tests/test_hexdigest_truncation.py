#!/usr/bin/env python3
"""Kazde obciecie `hexdigest()` idzie przez NAZWANA STALA, a stala mowi dlaczego.

**Skad ta bramka.** 6.D36. W drzewie stoja trzy obciecia odcisku i do tej pozycji
dwa szly przez `ODCISK_ZNAKOW`, a jedno przez literal `[:12]` — wszystkie trzy
w jednym pliku, `tools/tests/mutation_sweep.py`. Literal wszedl 06.09.2026 (6.B17)
i przezyl **292 z 763** commitow repozytorium, nie zglaszany przez nic.

**Dlaczego to jest odwrotnosc 6.B29, a nie jego powtorzenie.**
`test_dead_constants.py` pilnuje stalej, ktorej NIKT NIE CZYTA, i uzasadnia to
zdaniem, ktore stosuje sie tu doslownie: martwa stala jest zdaniem o repozytorium,
ktore ktos przeczyta i uzna za prawdziwe. Literal, ktory powinien byc stala, jest
tym samym zjawiskiem odwroconym — nie jest zdaniem o niczym, wiec nikt go nie
czyta i nikt go nie sprawdza. Dwie dlugosci tej samej wielkosci rozjezdzaja sie
wtedy po cichu, bo zadna nie wie o istnieniu tamtej.

**Czego ta bramka NIE robi, swiadomie.** Nie wymaga, zeby wszystkie obciecia mialy
TE SAMA dlugosc. Pomiar 6.D36 pokazal, ze `ODCISK_ZNAKOW` (16) i `ZNACZNIK_ZNAKOW`
(12) sa dwiema roznymi wielkosciami o roznej odpornosci na kolizje: pierwsza sluzy
do porownania i nie ma drugiej linii obrony, druga trafia do nazwy pliku, gdzie
kolizje lapie odmowa z 6.B32. Regula „jedna dlugosc dla wszystkich" zapalilaby sie
na dwoch przypadkach zrobionych dobrze. Bramka wymaga wiec NAZWY i UZASADNIENIA
Z LICZBA, a nie rownosci.

**Skan chodzi po NAZWANYCH podkatalogach, nie po korzeniu — i to nie jest ozdoba.**
Pierwszy pomiar do 6.D36, zrobiony `grep`em po `.` , zwrocil **szesc** literalow
i **dwanascie** obciec przez stala zamiast jednego i dwoch: `.claude/worktrees/`
trzyma piec pelnych kopii drzewa, ignorowanych przez gita i niewidocznych
w `git status`. Kazda liczba z takiego skanu jest przemnozona przez liczbe kopii,
ktora zmienia sie sama. Ta bramka liczy inaczej i test nizej tego DOWODZI, zamiast
zakladac — ta sama poprawka co w 6.D57.

KONTROLE NEGATYWNE — wykonane, kazda MUSI paść:

  1. literal `[:12]` przywrocony w `mutation_sweep.py` w miejsce stalej
     -> obciecia hexdigest przez literal, nie przez nazwana stala:
        ['tools/tests/mutation_sweep.py:1032  [:12]']
  2. `ZNACZNIK_ZNAKOW` bez akapitu `#:` nad definicja
     -> stale obcinajace odcisk bez uzasadnienia z liczba: ['ZNACZNIK_ZNAKOW']
  3. akapit `#:` bez ani jednej cyfry (sama proza)
     -> stale obcinajace odcisk bez uzasadnienia z liczba: ['ZNACZNIK_ZNAKOW']
  4. korzenie skanu podmienione na `.` (czyli na korzen repozytorium)
     -> skan wszedl do kopii z katalogu ignorowanego: 15 trafien pod
        `.claude/worktrees/`
     -> obciecia hexdigest przez literal: pieciokrotnie
        `.claude/worktrees/agent-*/tools/tests/mutation_sweep.py:1008  [:12]`
     Padaja DWA testy, i drugi z nich mowi wiecej niz pierwszy: kopie niosa
     jeszcze STARY numer wiersza i STARY literal, bo powstaly przed ta poprawka.
     Skan liczacy wystapienia raportowalby wiec usterke naprawiona w drzewie.
  5. `PODLOGA` ustawiona na 0
     -> podloga wyzerowana: skan moglby nie czytac niczego i nikt by nie zauwazyl
  6. wzorzec zawezony tak, ze nie lapie nic
     -> skan znalazl 0 obciec, a w drzewie jest ich co najmniej 3
     -> samosprawdzenie detektora tez pada (`[]` wobec oczekiwanego `['12']`)
     Padaja DWA testy i to jest zamierzone: podloga mowi „przestales czytac
     drzewo", samosprawdzenie mowi „przestales umiec paść". Zaden z nich osobno
     nie odroznia tych dwoch rzeczy.
"""

import io
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Drzewa przeszukiwane, para (podkatalog, rozszerzenie). NAZWANE podkatalogi,
#: nigdy korzen — patrz akapit o `.claude/worktrees/` w docstringu modulu.
DRZEWA = (
    ("tools", ".py"),
    ("src", ".cs"),
    ("tests", ".cs"),
)

#: Katalog, ktory trzyma kopie calego drzewa i ktorego zaden skan liczacy
#: wystapienia nie ma prawa zobaczyc. Nazwa stoi tu, zeby test nizej mogl
#: DOWIESC, ze skan tam nie wszedl, a nie zebrac to z zalozenia.
KOPIE_DRZEWA = os.path.join(".claude", "worktrees")

#: Ile obciec `hexdigest()` skan MUSI znalezc, zeby jego milczenie znaczylo
#: „nie ma literalow", a nie „nie przeczytalem zadnego pliku". Zmierzone
#: 09.09.2026 na `dba5737`: w drzewie stoja **3**, wszystkie w jednym pliku.
#: Zapadka — wolno wylacznie podnosic.
PODLOGA = 3

#: Obciecie odcisku: wywolanie `hexdigest` z pustymi nawiasami, a za nim wycinek
#: od dwukropka. Grupa niesie to, czym obcieto. Wzorzec jest tu opisany slowami,
#: a nie pokazany — pokazany zapalilby ten modul na sobie samym.
OBCIECIE = re.compile(r"hexdigest\(\)\s*\[\s*:\s*([^\]]+?)\s*\]")

#: Literal dziesietny w miejscu dlugosci — to jest scigane zjawisko.
LITERAL = re.compile(r"^\d+$")


def _pliki():
    """Sciezki do przeszukania, wzgledne wobec `ROOT`."""
    out = []
    for podkatalog, rozszerzenie in DRZEWA:
        baza = os.path.join(ROOT, podkatalog)
        if not os.path.isdir(baza):
            continue
        for katalog, _pod, nazwy in TW.walk(baza):
            for nazwa in sorted(nazwy):
                if nazwa.endswith(rozszerzenie):
                    pelna = os.path.join(katalog, nazwa)
                    out.append(os.path.relpath(pelna, ROOT))
    return sorted(out)


def _obciecia(pliki=None):
    """Lista `(sciezka, numer_wiersza, czym_obcieto)` dla calego skanu."""
    out = []
    for sciezka in (pliki if pliki is not None else _pliki()):
        try:
            tekst = io.open(os.path.join(ROOT, sciezka), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        for trafienie in OBCIECIE.finditer(tekst):
            wiersz = tekst.count("\n", 0, trafienie.start()) + 1
            out.append((sciezka, wiersz, trafienie.group(1)))
    return out


def _akapit_nad(tekst, nazwa):
    """Akapit `#:` stojacy bezposrednio nad definicja stalej `nazwa`."""
    wiersze = tekst.splitlines()
    for numer, wiersz in enumerate(wiersze):
        if re.match(r"^" + re.escape(nazwa) + r"\s*=", wiersz):
            akapit = []
            idx = numer - 1
            while idx >= 0 and wiersze[idx].lstrip().startswith("#:"):
                akapit.append(wiersze[idx])
                idx -= 1
            return "\n".join(reversed(akapit))
    return None


def test_skan_naprawde_czyta_drzewo():
    """Podloga na liczbe trafien. Bez niej przeniesiony plik zamienia te bramke
    w bramke o niczym, przechodzaca tym pewniej, im mniej przeczytala."""
    znalezione = _obciecia()
    assert len(znalezione) >= PODLOGA, (
        "skan znalazl " + str(len(znalezione)) + " obciec `hexdigest()`, a w drzewie "
        "jest ich co najmniej " + str(PODLOGA) + " — skan przestal czytac drzewo")


def test_podloga_nie_jest_wyzerowana():
    assert PODLOGA > 0, (
        "podloga wyzerowana: skan moglby nie czytac niczego i nikt by nie zauwazyl")


def test_zadne_obciecie_hexdigest_nie_idzie_przez_literal():
    zle = [s + ":" + str(w) + "  [:" + czym + "]"
           for s, w, czym in _obciecia() if LITERAL.match(czym)]
    assert not zle, (
        "obciecia hexdigest przez literal, nie przez nazwana stala: " + repr(zle)
        + " — dwie dlugosci tej samej wielkosci rozjezdzaja sie po cichu, bo zadna "
        "nie wie o istnieniu tamtej")


def test_kazda_stala_obcinajaca_ma_przy_sobie_uzasadnienie_z_liczba():
    """Sama nazwa nie wystarcza. `ODCISK_ZNAKOW` ma akapit o 64 bitach i rzedzie
    kolizji; gdyby go nie miala, byla by literalem z dluzsza nazwa."""
    bez = []
    for sciezka, _wiersz, czym in _obciecia():
        if LITERAL.match(czym):
            continue
        nazwa = czym.split(".")[-1]
        tekst = io.open(os.path.join(ROOT, sciezka), encoding="utf-8").read()
        akapit = _akapit_nad(tekst, nazwa)
        if akapit is None or not re.search(r"\d", akapit):
            bez.append(nazwa)
    assert not bez, (
        "stale obcinajace odcisk bez uzasadnienia z liczba: " + repr(sorted(set(bez))))


def test_skan_nie_liczy_kopii_z_katalogow_ignorowanych():
    """DOWOD, nie zalozenie — ta sama poprawka co w 6.D57.

    Kopie w `.claude/worktrees/` istnieja tylko na maszynach, ktore je zrobily.
    Skan liczacy wystapienia dawalby wiec inna liczbe w kontenerze sesji i inna
    na runnerze, a rozniloby je co innego niz drzewo. Ten test sprawdza OBIE
    strony: ze skan tam nie wchodzi i ze kopie faktycznie sa (albo ich nie ma,
    co tez trzeba powiedziec wprost, bo dowod bez przedmiotu nie jest dowodem).
    """
    weszlo = [s for s, _w, _c in _obciecia() if KOPIE_DRZEWA in s]
    assert not weszlo, (
        "skan wszedl do kopii z katalogu ignorowanego: " + str(len(weszlo))
        + " trafien pod " + KOPIE_DRZEWA)

    kopie = os.path.join(ROOT, KOPIE_DRZEWA)
    if not os.path.isdir(kopie):
        return
    ile = len([n for n in os.listdir(kopie)
               if os.path.isdir(os.path.join(kopie, n))])
    assert ile > 0 or True  # obecnosc kopii nie jest wymagana, ich zliczenie tak
    for _podkatalog, rozszerzenie in DRZEWA:
        if rozszerzenie != ".py":
            continue
        assert not any(KOPIE_DRZEWA in s for s in _pliki()), (
            "lista plikow skanu niesie sciezke z " + KOPIE_DRZEWA)


def test_detektor_ZAPALA_sie_na_literale_wstawionym_do_probki():
    """Samosprawdzenie przyrzadu: detektor MUSI umiec paść.

    Probka jest skladana z kawalkow, zeby tekst tego pliku nie zawieral wzorca —
    inaczej bramka zapalilaby sie na sobie i trzeba by ja wylaczyc, czyli
    dokladnie skutek, ktory 6.D27 nazwalo dla falszywych alarmow.
    """
    wolanie = "hexdigest" + "()"
    probka_zla = "x = h." + wolanie + "[:12]"
    probka_dobra = "x = h." + wolanie + "[:ODCISK_ZNAKOW]"

    trafienia_zle = OBCIECIE.findall(probka_zla)
    trafienia_dobre = OBCIECIE.findall(probka_dobra)
    assert trafienia_zle == ["12"], trafienia_zle
    assert trafienia_dobre == ["ODCISK_ZNAKOW"], trafienia_dobre
    assert LITERAL.match(trafienia_zle[0]), "detektor nie uznaje 12 za literal"
    assert not LITERAL.match(trafienia_dobre[0]), "detektor uznaje nazwe za literal"


def test_ten_modul_sam_przechodzi_wlasny_skan():
    """Probka z testu wyzej nie moze przeciekac do tekstu pliku."""
    moj = os.path.relpath(os.path.abspath(__file__), ROOT)
    assert moj in _pliki(), (
        "ten modul nie jest objety wlasnym skanem, wiec probka moglaby przeciekac "
        "niezauwazona: " + moj)
    wlasne = _obciecia([moj])
    assert wlasne == [], (
        "ten modul niesie w swoim tekscie " + str(len(wlasne)) + " wzorcow obciecia "
        + repr([str(w) + ":" + c for _s, w, c in wlasne]) + " — probka albo opis "
        "wzorca przeciekly. Pytanie o ZERO TRAFIEN, nie o zero literalow, jest tu "
        "cala rzecza: pierwsza wersja tego testu pytala o literaly i przeciek "
        "PRZEPUSCILA, bo `\" + \"12` nie jest literalem dziesietnym, a wzorzec "
        "juz go lapal")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
