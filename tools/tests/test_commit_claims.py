"""Co komunikat commita ZGLASZA wobec tego, co widac w jego diffie i w drzewie.

**Skad ta bramka.** 6.D275 zmierzylo, ze zdjecie pogrubienia zglasza kilkanascie
komunikatow, a w diffie widac ZERO — bo ruch zachodzi w drzewie roboczym przed
commitem. Jedyny slad zostaje w prozie komunikatu, a wszystkie czytniki tego drzewa
czytaja PLIKI. Ten sam ksztalt maja inne twierdzenia wpisywane wylacznie w komunikat:
„zapadka podniesiona", „kontrola negatywna czerwona", „liczby przeliczone".

Ta bramka **liczy** i pilnuje, zeby czytnik nie oslepl. Bramki ODRZUCAJACEJ commit
po tresci komunikatu tu nie ma i jest to wybor: komunikatu nie da sie poprawic bez
przepisania historii, wiec taka bramka ma zupelnie inny koszt i jest osobnym
rozstrzygnieciem.
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_tree_walks as TTW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Rejestr nazw zapadek POZYCZONY, a nie przepisany (6.D213). Wlasna lista nazw
#: starzalaby sie przy kazdej nowej zapadce i milczalaby o tym.
ZAPADKI = TTW.ZAPADKI

NAZWA_ZAPADKI = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(n) for n in
                             sorted(ZAPADKI, key=len, reverse=True)) + r")(?![\w])")

#: Zgloszeniem jest para WARTOSCI przy nazwie, a nie sam czasownik. Kotwica idzie
#: po NAZWIE i po ZDANIU, nigdy po wartosci liczbowej: dopasowanie liczby z prozy
#: do liczby z diffa daje falszywe trafienia i zmierzylo to juz 6.D275.
ZMIANA_DOKONANA = re.compile(r"(->|-->|→|\bz\s+`?\d+`?\s+(?:na|do)\s+`?\d+`?\b)")

#: Kotwica kontroli negatywnej w komunikacie.
#: Granica `(?!\d)` zamiast `\b` — bo `\b` nie jest granica liczby (6.D277), a nowy
#: wzorzec pisze sie od razu poprawnie, zeby nie dokladac do zbioru, ktory tamta
#: pozycja wlasnie przybila. Granica jest tu WEZSZA niz `(?![\d,.])` i to jest
#: poprawka z pierwszego przebiegu: przy `(?![\d,.])` etykieta `KN-1` konczaca
#: zdanie KROPKA przestawala sie lapac, bo kropka zdaniowa nie jest separatorem
#: dziesietnym — populacja spadla o jeden i zlapala to podloga, a nie ja.
KONTROLA_NEGATYWNA = re.compile(r"kontrol\w*\s+negatywn\w*|\bKN-\d+(?!\d)",
                                re.IGNORECASE)

#: Slad WYKONANIA obok kotwicy. Pole „Wyjscie" tej pozycji mowi „zglasza WYKONANA
#: kontrole negatywna", a nie „wspomina o kontroli" — i roznica jest mierzalna:
#: bez tego warunku populacja jest o kilkanascie wieksza. Granica „zglasza wykonana"
#: wobec „wspomina" jest wiec PROGIEM CZYTNIKA, a nie faktem w drzewie, i tak jest
#: zapisana w raporcie.
WYNIK_KONTROLI = re.compile(
    r"czerwie|zielen|zieleń|FAIL|przesz[lł]|\d+\s*/\s*\d+|kod\s+\d|"
    r"->|→|zmierzon|wykonan|padł|padl|zapali|nie zapal", re.IGNORECASE)

#: Okno wokol kotwicy kontroli, w ktorym szuka sie sladu wykonania.
OKNO_KONTROLI = 400

#: `--diff-merges=first-parent` przy czytaniu diffow jest TRESCIA, a nie wygoda:
#: domyslnie `git log -p` POMIJA diff scalenia w calosci, a scalenia tego
#: repozytorium niosa w komunikacie te same zgloszenia co commity galezi. Bez tego
#: przelacznika kilkanascie scalen wpada do pary „zgloszone bez widocznego"
#: z powodu czysto technicznego. Zmierzone przy 6.D279, nie przewidziane.
DIFF_SCALENIA = "--diff-merges=first-parent"

#: Przypisanie stalej w wierszu diffa — ksztalt `+NAZWA = wartosc`.
PRZYPISANIE_W_DIFFIE = re.compile(r"^([+-])\s*([A-Z][A-Z0-9_]*)\s*=\s*\S")

#: Sciezka pliku w diffie i ksztalt sladu kontroli negatywnej w drzewie:
#: raport w `reports/` albo plik testu.
SCIEZKA_W_DIFFIE = re.compile(r"^diff --git a/(\S+) b/\S+$")
SLAD_KONTROLI = re.compile(r"^reports/.*\.md$|(^|/)test_[^/]*\.py$|Tests?\.cs$")

#: Okno wokol nazwy zapadki, w ktorym szuka sie pary wartosci. Jedno zdanie bywa
#: dluzsze niz nazwa plus strzalka, a caly komunikat jest za szeroki: przy calym
#: komunikacie kazda nazwa wymieniona gdziekolwiek liczylaby sie jako zgloszenie.
OKNO_PRZED = 75
OKNO_PO = 100

#: Podlogi na cztery populacje. PODLOGI, bo historia tylko rosnie — commitow nie
#: ubywa, wiec rownosc czerwienialaby przy kazdym nowym commicie. Bronia przed
#: jedna rzecza: czytnikiem, ktory oslepl i odpowiada zerem tak samo jak widzacy
#: (6.D27). Zmierzone 18.09.2026 na wierzcholku `main`.
MIN_ZGLASZA_ZMIANE_ZAPADKI = 218
MIN_ZGLASZA_I_WIDAC = 217
MIN_ZGLASZA_KONTROLE = 468
MIN_ZGLASZA_KONTROLE_ZE_SLADEM = 464

#: Podloga na wariant SZEROKI kotwicy A — pare wartosci przyjmuje sie takze przed
#: nazwa. Stoi tu, zeby czulosc kotwicy byla PRZYBITA, a nie opisana: gdyby oba
#: warianty zaczely dawac to samo, sito przestaloby rozrozniac to, co rozroznia dzis.
MIN_ZGLASZA_SZEROKO = 225

#: Commit, ktorego komunikat ZGLASZA podniesienie zapadki, a diff jej nie rusza.
#: Kontrola negatywna sita: bez niej sito mierzy zgodnosc, ktorej nie sprawdza.
COMMIT_ZGLOSZONE_BEZ_WIDOCZNEGO = "8ae17c40"

#: Commit, ktory zapadke w diffie RUSZA, a w komunikacie nie wymienia jej ani razu.
#: Kontrola przyrzadu: ma trafic do pary ODWROTNEJ, a nie wypasc z obu.
COMMIT_WIDOCZNE_BEZ_ZGLOSZONEGO = "d833c41c"

#: Commit, w ktorym kontrola negatywna ZOSTALA wykonana, a komunikat nie mowi
#: o niej ani slowem — zlapany na wlasnym commicie tej serii. Kontrola przyrzadu
#: w druga strone: sito ma go NIE liczyc, bo liczy zgloszenia, a nie wykonania.
COMMIT_KONTROLA_BEZ_ZGLOSZENIA = "4a9529f"


def _git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args),
                          capture_output=True, text=True, check=True,
                          errors="replace").stdout


def zglaszane_zapadki(komunikat, szerokie=False):
    """Nazwy zapadek, przy ktorych komunikat stawia PARE WARTOSCI.

    Domyslnie para musi stac PO nazwie. Wariant `szerokie` przyjmuje ja takze
    przed nazwa — i roznica miedzy nimi jest ZMIERZONA, a nie zalozona: sito
    szerokie daje populacje wieksza, bo pare wartosci stojaca przy JEDNEJ nazwie
    przypisuje takze nazwie sasiedniej. Obie liczby stoja w raporcie, zeby nie
    trzeba bylo zgadywac, ktora policzono.
    """
    out = set()
    for trafienie in NAZWA_ZAPADKI.finditer(komunikat):
        lo = max(0, trafienie.start() - OKNO_PRZED) if szerokie else trafienie.end()
        hi = min(len(komunikat), trafienie.end() + OKNO_PO)
        if ZMIANA_DOKONANA.search(komunikat[lo:hi]):
            out.add(trafienie.group(1))
    return out


def zglasza_wykonana_kontrole(komunikat):
    """Czy komunikat zglasza kontrole negatywna WYKONANA, a nie tylko wspomina."""
    for trafienie in KONTROLA_NEGATYWNA.finditer(komunikat):
        lo = max(0, trafienie.start() - OKNO_KONTROLI)
        hi = min(len(komunikat), trafienie.end() + OKNO_KONTROLI)
        if WYNIK_KONTROLI.search(komunikat[lo:hi]):
            return True
    return False


def komunikaty(root):
    """`{sha: komunikat}` — osobny, tani przebieg po samych komunikatach.

    Komunikat i diff czytane SA OSOBNO, i to jest poprawka z pierwszego przebiegu,
    a nie ostroznosc: przy jednym przebiegu format `%H` bez `%B` dal komunikaty
    puste, populacja wyszla ZERO, a podloga nizej zapalila sie i nazwala to
    oslepnieciem czytnika. Nazwala trafnie.
    """
    out = {}
    for blok in _git("log", "--format=%x01%H%x02%B").split("\x01"):
        if not blok.strip():
            continue
        sha, _, tresc = blok.partition("\x02")
        out[sha.strip()] = tresc
    return out


def strumien_diffow(root):
    """(sha, zapadki_w_diffie, pliki_diffa) dla kazdego commita, strumieniem."""
    proces = subprocess.Popen(
        ["git", "-C", root, "log", "--format=%x01%H", "--unified=0", "-p",
         "--no-color", "-M", DIFF_SCALENIA],
        stdout=subprocess.PIPE, text=True, errors="replace", bufsize=1 << 20)
    sha, zapadki, pliki = None, set(), set()
    try:
        for wiersz in proces.stdout:
            if wiersz.startswith("\x01"):
                if sha is not None:
                    yield sha, zapadki, pliki
                sha = wiersz[1:].strip()
                zapadki, pliki = set(), set()
                continue
            trafienie = SCIEZKA_W_DIFFIE.match(wiersz.rstrip("\n"))
            if trafienie:
                pliki.add(trafienie.group(1))
                continue
            trafienie = PRZYPISANIE_W_DIFFIE.match(wiersz)
            if trafienie and trafienie.group(2) in ZAPADKI:
                zapadki.add(trafienie.group(2))
        if sha is not None:
            yield sha, zapadki, pliki
    finally:
        proces.stdout.close()
        proces.wait()


def cztery_populacje(root):
    """Dwie pary „zgloszone" wobec „widoczne" — i adresy commitow kazdej z nich."""
    zglasza_zapadke, zglasza_i_widac = [], []
    zglasza_kontrole, zglasza_kontrole_ze_sladem = [], []
    widoczne_bez_zgloszonego = []
    teksty = komunikaty(root)
    for sha, w_diffie, pliki in strumien_diffow(root):
        komunikat = teksty.get(sha, "")
        zgloszone = zglaszane_zapadki(komunikat)
        if zgloszone:
            zglasza_zapadke.append(sha)
            if zgloszone & w_diffie:
                zglasza_i_widac.append(sha)
        elif w_diffie and not NAZWA_ZAPADKI.search(komunikat):
            widoczne_bez_zgloszonego.append(sha)
        if zglasza_wykonana_kontrole(komunikat):
            zglasza_kontrole.append(sha)
            if any(SLAD_KONTROLI.search(p) for p in pliki):
                zglasza_kontrole_ze_sladem.append(sha)
    return {
        "zglasza_zapadke": zglasza_zapadke,
        "zglasza_i_widac": zglasza_i_widac,
        "zglasza_kontrole": zglasza_kontrole,
        "zglasza_kontrole_ze_sladem": zglasza_kontrole_ze_sladem,
        "widoczne_bez_zgloszonego": widoczne_bez_zgloszonego,
    }


def test_cztery_liczby_ktorych_zadalo_pole_wyjscie():
    """**Dwie pary „zgloszone" wobec „widoczne" — z historii, nie wpisane.**

    Podlogi, a nie rownosci: commitow tylko przybywa, wiec rownosc czerwienialaby
    przy kazdym nowym commicie — czyli przy pracy poprawnej (6.D27).
    """
    p = cztery_populacje(ROOT)
    a1, a2 = len(p["zglasza_zapadke"]), len(p["zglasza_i_widac"])
    b1, b2 = len(p["zglasza_kontrole"]), len(p["zglasza_kontrole_ze_sladem"])
    # Kazda zapadka stoi w asercji GOLA NAZWA, a nie jako element krotki w petli:
    # klasyfikator klas zapadek czyta `ast.Name`, wiec przez petle nie widzi ich
    # wcale i wypisuje `poza skanem` — czyli „nie pilnuje ich nic" o progu, ktory
    # pilnuje. Zlapala to bramka klas, nie ja.
    assert a1 >= MIN_ZGLASZA_ZMIANE_ZAPADKI, (
        "komunikatow zglaszajacych zmiane zapadki jest %d przy podlodze %d — "
        "czytnik oslepl albo historia zostala przepisana"
        % (a1, MIN_ZGLASZA_ZMIANE_ZAPADKI))
    assert a2 >= MIN_ZGLASZA_I_WIDAC, (
        "z tego widocznych w diffie jest %d przy podlodze %d" % (a2, MIN_ZGLASZA_I_WIDAC))
    assert b1 >= MIN_ZGLASZA_KONTROLE, (
        "komunikatow zglaszajacych WYKONANA kontrole negatywna jest %d przy "
        "podlodze %d" % (b1, MIN_ZGLASZA_KONTROLE))
    assert b2 >= MIN_ZGLASZA_KONTROLE_ZE_SLADEM, (
        "z tego ze sladem w drzewie jest %d przy podlodze %d"
        % (b2, MIN_ZGLASZA_KONTROLE_ZE_SLADEM))
    assert a2 <= a1, (
        "commitow `zgloszone i widoczne` jest wiecej niz `zgloszonych` — sito "
        "liczy podzbior wiekszy od zbioru, czyli czyta dwie rozne populacje")
    assert b2 <= b1, (
        "commitow `kontrola ze sladem` jest wiecej niz `zglaszajacych kontrole`")


def test_komunikat_zglaszajacy_zapadke_ktorej_diff_NIE_rusza_jest_zgloszony():
    """**Kontrola negatywna sita, na commicie z drzewa, a nie syntetycznym.**

    Bez tej polowy sito mierzy zgodnosc, ktorej nie sprawdza: zliczaloby
    „zgloszone" i „widoczne" jako te sama liczbe i roznica nie moglaby wyjsc.
    """
    p = cztery_populacje(ROOT)
    skroty = {s[:7] for s in p["zglasza_zapadke"]}
    widac = {s[:7] for s in p["zglasza_i_widac"]}
    klucz = COMMIT_ZGLOSZONE_BEZ_WIDOCZNEGO[:7]
    assert klucz in skroty, (
        "commit %s nie trafil do `zglaszajacych zmiane zapadki`, a jego komunikat "
        "ja zglasza — sito nie widzi zgloszenia" % klucz)
    assert klucz not in widac, (
        "commit %s trafil do `zgloszone i widoczne`, a jego diff zapadki nie rusza "
        "— sito uznaje za widoczne cos, czego w diffie nie ma" % klucz)


def test_commit_zmieniajacy_zapadke_BEZ_wzmianki_trafia_do_pary_odwrotnej():
    """**Kontrola przyrzadu: ma trafic do pary ODWROTNEJ, a nie wypasc z obu.**

    Sito, ktore takiego commita gubi, mierzy wylacznie to, co autorzy napisali,
    i o ruchu niezglaszanym nie powie nic.
    """
    p = cztery_populacje(ROOT)
    odwrotna = {s[:7] for s in p["widoczne_bez_zgloszonego"]}
    zglaszane = {s[:7] for s in p["zglasza_zapadke"]}
    klucz = COMMIT_WIDOCZNE_BEZ_ZGLOSZONEGO[:7]
    assert klucz in odwrotna, (
        "commit %s wypadl z pary odwrotnej — jego diff rusza zapadke, a komunikat "
        "nie wymienia jej ani razu, wiec ma tam stac" % klucz)
    assert klucz not in zglaszane, (
        "commit %s uznany za zglaszajacy, a jego komunikat nazwy zapadki nie "
        "zawiera — sito czyta cos innego niz komunikat" % klucz)


def test_kontrola_WYKONANA_ale_niezgloszona_NIE_jest_liczona_jako_zgloszenie():
    """**Kontrola przyrzadu w druga strone — zlapana na wlasnym commicie serii.**

    Kontrola negatywna zostala w tym commicie wykonana i jej wyjscie stoi
    w raporcie, a komunikat nie mowi o niej ani slowem. Sito liczy ZGLOSZENIA,
    wiec ma go NIE liczyc — inaczej mierzy wykonania, o ktorych nic nie wie.
    """
    p = cztery_populacje(ROOT)
    zgloszone = {s[:7] for s in p["zglasza_kontrole"]}
    klucz = COMMIT_KONTROLA_BEZ_ZGLOSZENIA[:7]
    assert klucz not in zgloszone, (
        "commit %s policzony jako zglaszajacy kontrole negatywna, a jego komunikat "
        "slowa `kontrol` nie zawiera ani razu — sito zglasza wiecej, niz w tekscie "
        "stoi" % klucz)
    komunikat = _git("log", "-1", "--format=%B", COMMIT_KONTROLA_BEZ_ZGLOSZENIA)
    assert not KONTROLA_NEGATYWNA.search(komunikat), (
        "kotwica kontroli negatywnej trafia w komunikat %s — przypadek przestal "
        "byc tym, czym byl, wiec zamien go na inny ZYWY i powiedz o tym" % klucz)


def test_szerokosc_kotwicy_ZMIENIA_liczbe_i_roznica_jest_zmierzona():
    """**Czulosc sita jest przybita, a nie opisana slowem.**

    Kotwica waska zada pary wartosci PO nazwie, szeroka przyjmuje ja takze przed.
    Roznica nie jest drobiazgiem: sito szerokie przypisuje pare stojaca przy jednej
    nazwie takze nazwie sasiedniej, a w tym repozytorium komunikat wymieniajacy
    kilka podniesionych zapadek naraz jest zwyklym ksztaltem. Gdyby oba warianty
    dawaly to samo, znaczyloby to, ze jeden z nich przestal czytac to, co czyta.
    """
    teksty = komunikaty(ROOT)
    szeroko = sum(1 for k in teksty.values() if zglaszane_zapadki(k, szerokie=True))
    wasko = sum(1 for k in teksty.values() if zglaszane_zapadki(k))
    assert szeroko >= MIN_ZGLASZA_SZEROKO, (
        "wariant szeroki daje %d przy podlodze %d — czytnik oslepl"
        % (szeroko, MIN_ZGLASZA_SZEROKO))
    assert szeroko > wasko, (
        "wariant szeroki daje %d, a waski %d — sito przestalo rozrozniac pare "
        "wartosci stojaca PRZED nazwa od stojacej PO niej, wiec obie liczby "
        "w raporcie mowia odtad o tym samym" % (szeroko, wasko))


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
