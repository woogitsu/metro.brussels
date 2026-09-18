"""Zdania, ktore sa JEDNO ZDJECIE POGRUBIENIA od zniknięcia z obu sit.

**Skad ta bramka.** `MAX_POGRUBIONYCH_BEZ_POKRYCIA` dopuszcza dwa lekarstwa: policz
liczbe w kodzie albo zdejmij pogrubienie. 6.D275 mialo nadac drugiemu cene, wiazac je
z `MAX_GOLYCH_W_PROZIE_POMIAROWEJ` — i nadaje ja tylko wtedy, gdy zdanie zachowa INNA
liczbe pogrubiona albo stoi w akapicie z zapowiedzia pomiaru. Gdy pogrubiona byla
w zdaniu JEDYNA, zdjecie wyprowadza CALE ZDANIE z populacji i liczba znika spod obu
sit naraz: populacja SPADA, zamiast urosnac. Zapadka jest gorna, wiec spadek
przechodzi ja celujaco — ten sam ksztalt co 6.D27, tylko od strony populacji.

Ta bramka **mierzy dziure i przybija jej rozmiar**, a nie lata jej. Latanie znaczyloby
poszerzenie `ZAPOWIEDZ_POMIARU`, a to jest odrzucone pomiarem w 6.D275 i byloby
osobnym rozstrzygnieciem.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_message_claims as TMC  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Plik tej bramki. Odejmowany od populacji, bo proza tego modulu ma dokladnie ten
#: ksztalt, ktory modul mierzy — bez odjecia liczba mowilaby o WLASNYM PRZYRZADZIE.
#: Odjecie jest jawne i pilnowane osobnym testem, tak samo jak w 6.D277.
TEN_MODUL = "test_one_bold_sentences.py"

#: Rewizje, na ktorych policzono koszt obu podlog nizej: cala historia
#: `tools/tests/`, kazda rewizja porownana ze SWOIM PIERWSZYM RODZICEM.
#: Zakotwiczenie na rodzicu jest tu trescia, a nie ostroznoscia: liczenie roznic
#: miedzy kolejnymi pozycjami `git rev-list` daje ARTEFAKT PORZADKU, bo `rev-list`
#: przeplata galezie — ta sama historia dala wtedy koszt zawyzony siedmiokrotnie.
REWIZJI_W_POMIARZE_KOSZTU = 664

#: Ile razy w tych rewizjach spadla populacja zdan, a ile — populacja liczb golych.
#: Obie zmierzone jako praca uprawniona: raz zdanie z nieprawdziwa liczba skasowano
#: przy scalaniu, raz proze przepisano na liste. Spadku typu „zdaniu przybyla DRUGA
#: pogrubiona" — ksztaltu, ktorego balem sie najbardziej, bo zapalalby sie na pracy
#: poprawnej — nie ma w tej historii ANI JEDNEGO.
SPADKOW_ZDAN_W_HISTORII = 2
SPADKOW_GOLYCH_W_HISTORII = 1

#: Podloga na liczbe zdan o JEDNEJ pogrubionej, stojacych poza zapowiedzia pomiaru.
#: Kazde z nich jest jedno zdjecie gwiazdek od wyjscia spod OBU sit. Koszt tej
#: podlogi jest POLICZONY, a nie oszacowany — stale wyzej — i jest tego samego
#: rzedu co koszt, ktory 6.D270 policzylo i ktory zostal przyjety.
MIN_ZDAN_O_JEDNEJ_POGRUBIONEJ = 132

#: Podloga na liczby GOLE stojace w tych wlasnie zdaniach. Znikna razem ze zdaniem,
#: wiec to one nadaja zdjeciu pogrubienia cene mierzalna.
MIN_GOLYCH_W_TYCH_ZDANIACH = 96


def zdania_o_jednej_pogrubionej(root):
    """`[(plik, wiersz, zdanie)]` — zdania o DOKLADNIE JEDNEJ liczbie pogrubionej.

    Czytnik jest POZYCZONY z `test_message_claims` co do wzorca i co do jednostki
    (6.D213): ta sama `proza`, ten sam `SPECYFIKATOR`, te same `_akapity_prozy`,
    `ZAPOWIEDZ_POMIARU`, `POGRUBIONA`, `GRANICA_ZDANIA` i `DATA`. Druga kopia sita
    mowilaby o czym innym niz zapadka, ktorej dziure ta bramka mierzy.

    `root` jest argumentem JAWNYM: domyslny wiaze sie przy imporcie, wiec podmiana
    `modul.ROOT` jest no-opem, a cztery identyczne odczyty czytaja sie jak wynik
    (6.D265, 6.D269).
    """
    out = []
    for nazwa, wiersz, tekst, _rodzaj, _od, _do in TMC.proza(None, root):
        if nazwa == TEN_MODUL:
            continue
        czysty = TMC.SPECYFIKATOR.sub(" ", tekst)
        for akapit in TMC._akapity_prozy(czysty):
            # Akapit z zapowiedzia trzyma zdanie w populacji NIEZALEZNIE od pogrubien,
            # wiec zdjecie gwiazdek go stamtad nie wyprowadza — i dlatego wypada.
            if TMC.ZAPOWIEDZ_POMIARU.search(akapit):
                continue
            for zdanie in TMC.GRANICA_ZDANIA.split(akapit):
                if TMC.DATA.search(zdanie):
                    continue
                if len(TMC.POGRUBIONA.findall(zdanie)) == 1:
                    out.append((nazwa, wiersz, zdanie))
    return out


def gole_w_tych_zdaniach(root):
    """Liczby gole stojace w zdaniach z listy wyzej — z wyniku zapadki, nie liczone."""
    klucze = {(n, w, z) for n, w, z in zdania_o_jednej_pogrubionej(root)}
    return [g for g in TMC.gole_w_prozie_pomiarowej(None, root)
            if (g[0], g[1], g[3]) in klucze]


def test_ile_zdan_jest_jedno_zdjecie_od_znikniecia():
    """**Dwie z trzech liczb, ktorych zadalo pole „Wyjscie" — z drzewa, nie wpisane.**

    PODLOGI, a nie rownosci: populacja rosnie z kazdym nowym zdaniem prozy, wiec
    przybicie czerwienialoby przy pracy poprawnej (6.D27). Podloga milczy na wzroscie,
    bo wzrost tylko ja oddala, a lapie SPADEK — czyli dokladnie to, czego zapadka
    gorna nie widzi.
    """
    zdania = zdania_o_jednej_pogrubionej(ROOT)
    pliki = {nazwa for nazwa, _w, _z in zdania}
    assert len(zdania) >= MIN_ZDAN_O_JEDNEJ_POGRUBIONEJ, (
        "zdan o JEDNEJ pogrubionej liczbie, poza akapitem z zapowiedzia, jest %d "
        "przy podlodze %d (w %d plikach). Spadek znaczy, ze ktoremus zdaniu zdjeto "
        "pogrubienie — a wtedy liczba znika spod OBU sit naraz i zapadka gorna "
        "`MAX_GOLYCH_W_PROZIE_POMIAROWEJ` przechodzi na zielono nie dlatego, ze jest "
        "dobrze. Jesli zdjecie jest uprawnione, obniz podloge W TYM SAMYM COMMICIE "
        "i dopisz powod. Koszt tej podlogi zmierzony na %d rewizjach: %d spadki."
        % (len(zdania), MIN_ZDAN_O_JEDNEJ_POGRUBIONEJ, len(pliki),
           REWIZJI_W_POMIARZE_KOSZTU, SPADKOW_ZDAN_W_HISTORII))

    gole = gole_w_tych_zdaniach(ROOT)
    assert len(gole) >= MIN_GOLYCH_W_TYCH_ZDANIACH, (
        "liczb golych stojacych w tych zdaniach jest %d przy podlodze %d — to one "
        "znikaja razem ze zdaniem i to one nadaja zdjeciu pogrubienia cene. Koszt "
        "zmierzony na %d rewizjach: %d spadek. Adresy: %s"
        % (len(gole), MIN_GOLYCH_W_TYCH_ZDANIACH,
           REWIZJI_W_POMIARZE_KOSZTU, SPADKOW_GOLYCH_W_HISTORII,
           [(x[0], x[2]) for x in gole[:5]]))


def test_zdanie_z_DWIEMA_pogrubionymi_NIE_trafia_na_liste():
    """**Kontrola przyrzadu: jedno zdjecie ma NIE wyprowadzac zdania z populacji.**

    Zdanie z dwiema pogrubionymi zostaje po zdjeciu jednej nadal pogrubione, wiec
    caly mechanizm, ktory ta bramka mierzy, go nie dotyczy. Sito, ktore go liczy,
    zglasza populacje wieksza niz dziura i liczba przestaje cokolwiek znaczyc.
    """
    jedna = "Razem **27** metod bylo dla bramki niewidzialne."
    dwie = "Wychodzi **2,06** wobec **2,94**, wiec gra pinuje gesciej."
    assert len(TMC.POGRUBIONA.findall(jedna)) == 1, (
        "czytnik pogrubien nie widzi jednej pogrubionej tam, gdzie stoi jedna: %s"
        % TMC.POGRUBIONA.findall(jedna))
    assert len(TMC.POGRUBIONA.findall(dwie)) == 2, (
        "czytnik pogrubien nie widzi dwoch pogrubionych tam, gdzie stoja dwie: %s"
        % TMC.POGRUBIONA.findall(dwie))

    zdania = {z for _n, _w, z in zdania_o_jednej_pogrubionej(ROOT)}
    z_dwiema = [z for z in zdania if len(TMC.POGRUBIONA.findall(z)) != 1]
    assert z_dwiema == [], (
        "na liscie stanelo zdanie, ktore nie ma DOKLADNIE jednej pogrubionej: %s"
        % z_dwiema[:3])


def test_czytnik_widzi_przypadek_ktory_pozycje_wywolal():
    """**Sprawdzenie na zywej instancji z drzewa, a nie na przykladzie.**

    Bez tego sito moze byc zgodne samo ze soba i slepe na ksztalt, ktory pozycje
    wywolal — a taki wynik czyta sie dokladnie jak poprawny (6.D276).
    """
    zdania = zdania_o_jednej_pogrubionej(ROOT)
    z_golymi = [g for g in gole_w_tych_zdaniach(ROOT)]
    assert z_golymi, (
        "ani jedno zdanie z listy nie niesie liczby golej — wtedy zdjecie "
        "pogrubienia nie ma mierzalnej ceny i ta bramka nie mierzy nic")

    #: Zdanie, na ktorym 6.D275 zlapalo dziure: pogrubiona jest w nim jedyna,
    #: a obok stoi ta sama liczba goła — po zdjeciu gwiazdek znikaja OBIE.
    wywolujace = [(n, z) for n, _w, z in zdania
                  if n == "csharp_assertions.py" and "NIEROZSTRZYGNIETE" in z]
    assert wywolujace, (
        "zdania, ktore pozycje wywolalo, nie ma na liscie — sito jest zgodne samo "
        "ze soba i slepe na przypadek, ktory je stworzyl. Jesli proza tego modulu "
        "zostala przepisana, zamien kotwice na inna ZYWA instancje i powiedz o tym")


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
