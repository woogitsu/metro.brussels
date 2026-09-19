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
import tempfile

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

#: Raport w diffie. `SLAD_KONTROLI` wyzej przyjmuje TAKZE plik testu, a 6.D283
#: rozroznia commit dopisujacy raport od commita, ktory dopisuje wylacznie plik
#: testu — potrzebny jest wiec wzorzec wezszy, a nie ten sam.
RAPORT_W_DIFFIE = re.compile(r"^reports/.*\.md$")

#: Nazwa modulu testowego w prozie. Zapadki czyta `NAZWA_ZAPADKI` z rejestru
#: POZYCZONEGO, a modulow rejestru nie ma — wlasna lista nazw starzalaby sie przy
#: kazdym nowym module i milczalaby o tym, wiec tu stoi wzorzec.
NAZWA_MODULU = re.compile(r"\btest_[a-z0-9_]+\.py\b")

#: Nazwy stojace w tym repozytorium w niemal kazdym komunikacie i w niemal kazdym
#: raporcie: polecenie weryfikacji `test_all.py` i zapadka `MIN_REPORTS`, ktora
#: podnosi kazdy commit dopisujacy raport. Zgodnosc oparta WYLACZNIE na nich nie
#: mowi o tym, ze raport opisuje TE kontrole — dlatego takie commity sa liczone
#: osobno, a nie wyrzucane: wyrzucenie byloby ocena, osobne liczenie jest pomiarem.
WSZECHOBECNE_NAZWY = frozenset({"MIN_REPORTS", "test_all.py"})

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

#: Trzy klasy sladu (6.D283), zmierzone 19.09.2026 na wierzcholku `main`. PODLOGI
#: z tego samego powodu co wyzej: kazda klasa tylko rosnie, bo commitow nie ubywa.
#: Wariant WASKI porownuje raport z oknem wokol kotwicy kontroli, SZEROKI — z calym
#: komunikatem; roznica miedzy nimi jest przybita asercja, a nie opisana slowem.
MIN_SLAD_DOTYCZY_WASKO = 154
MIN_SLAD_DOTYCZY_SZEROKO = 224
MIN_SLAD_BEZ_RAPORTU = 113

#: Commit, ktorego komunikat zglasza kontrole negatywna i ktory dopisuje raport,
#: ale raport nazywa co INNEGO niz okno kontroli: w oknie stoi `MINIMUM_DETAIL_BLOCKS`
#: (zapadka podniesiona przy okazji), w dopisanym raporcie — `test_field_paths.py`.
#: Kontrola negatywna zaciesnienia: dzisiejsze `SLAD_KONTROLI` liczy go jako slad,
#: a klasa `dotyczy` ma go NIE zawierac.
COMMIT_SLAD_O_CZYM_INNYM = "c78b34a7"

#: Commit, ktorego raport wymienia te sama zapadke co okno kontroli
#: (`MIN_WIERSZY_Z_ARYTMETYKA`). Kontrola przyrzadu: ma w klasie `dotyczy` ZOSTAC,
#: i to nie za sprawa nazw wszechobecnych.
COMMIT_SLAD_TEJ_SAMEJ = "bb370e82"

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


#: Pamiec na wyniki obu czytnikow historii. Kazde wywolanie to osobny przebieg
#: `git log -p` po calej historii, a testy nizej pytaja o te same liczby po kilka
#: razy — bez pamieci modul chodzi 31 s, z pamiecia 7 s (zmierzone 19.09.2026,
#: 6.D283; przed ta pozycja, przy pieciu testach, chodzil 9 s — czyli testow jest
#: dwa razy wiecej, a czasu mniej). Klucz niesie KOMPLET argumentow, wiec pamiec
#: nie odpowiada na inne pytanie niz zadane.
_PAMIEC = {}


def _git(*args, root=ROOT):
    return subprocess.run(["git", "-C", root] + list(args),
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
    for blok in _git("log", "--format=%x01%H%x02%B", root=root).split("\x01"):
        if not blok.strip():
            continue
        sha, _, tresc = blok.partition("\x02")
        out[sha.strip()] = tresc
    return out


def strumien_diffow(root):
    """(sha, zapadki_w_diffie, pliki_diffa, dopisane_do_raportow) — strumieniem.

    Czwarty element to sklejona TRESC wierszy DOPISANYCH w plikach `reports/*.md`
    tego commita. Czytana jest z tego samego przebiegu `git log -p`, a nie
    z osobnego `git show` na kazdym commicie: osobny przebieg to kilkaset procesow
    i te sama tresc, tylko drozej.
    """
    proces = subprocess.Popen(
        ["git", "-C", root, "log", "--format=%x01%H", "--unified=0", "-p",
         "--no-color", "-M", DIFF_SCALENIA],
        stdout=subprocess.PIPE, text=True, errors="replace", bufsize=1 << 20)
    sha, zapadki, pliki = None, set(), set()
    biezacy, dopisane = None, []
    try:
        for wiersz in proces.stdout:
            if wiersz.startswith("\x01"):
                if sha is not None:
                    yield sha, zapadki, pliki, "".join(dopisane)
                sha = wiersz[1:].strip()
                zapadki, pliki = set(), set()
                biezacy, dopisane = None, []
                continue
            trafienie = SCIEZKA_W_DIFFIE.match(wiersz.rstrip("\n"))
            if trafienie:
                pliki.add(trafienie.group(1))
                biezacy = trafienie.group(1)
                continue
            if (biezacy and RAPORT_W_DIFFIE.match(biezacy)
                    and wiersz.startswith("+") and not wiersz.startswith("+++")):
                dopisane.append(wiersz[1:])
            trafienie = PRZYPISANIE_W_DIFFIE.match(wiersz)
            if trafienie and trafienie.group(2) in ZAPADKI:
                zapadki.add(trafienie.group(2))
        if sha is not None:
            yield sha, zapadki, pliki, "".join(dopisane)
    finally:
        proces.stdout.close()
        proces.wait()


def nazwy_modulow_i_zapadek(tekst):
    """Nazwy, po ktorych porownuje sie komunikat z raportem (6.D283)."""
    return set(NAZWA_MODULU.findall(tekst)) | {
        t.group(1) for t in NAZWA_ZAPADKI.finditer(tekst)}


def okno_wokol_kontroli(komunikat):
    """Fragmenty komunikatu wokol kotwic kontroli negatywnej, sklejone.

    Okno jest to samo, ktore `zglasza_wykonana_kontrole` przeszukuje w poszukiwaniu
    sladu wykonania — pozyczone, a nie przepisane, zeby obie polowy mowily
    o TYM SAMYM kawalku tekstu.
    """
    kawalki = []
    for trafienie in KONTROLA_NEGATYWNA.finditer(komunikat):
        lo = max(0, trafienie.start() - OKNO_KONTROLI)
        hi = min(len(komunikat), trafienie.end() + OKNO_KONTROLI)
        kawalki.append(komunikat[lo:hi])
    return "\n".join(kawalki)


def klasy_sladu(root, szeroko=False):
    """Trzy klasy sladu w populacji „zglasza kontrole i ma slad" (6.D283).

    Dzisiejsze `SLAD_KONTROLI` sprawdza, czy w commicie STOI raport albo plik
    testu — a nie, czy ten raport mowi o kontroli, ktora zglasza komunikat.
    Ta funkcja zaciesnia kryterium i dzieli populacje na:

    * `dotyczy` — raport dopisany w tym samym commicie wymienia nazwe modulu
      albo zapadki, ktora wymienia takze komunikat,
    * `nic_wspolnego` — raport jest, a wspolnej nazwy nie ma,
    * `bez_raportu` — commit raportu nie dopisuje, slad jest samym plikiem testu.

    `szeroko` przelacza strone komunikatu z okna wokol kontroli na caly komunikat.
    Rozbicie `nic_wspolnego` na trzy przyczyny jest tu dlatego, ze sama liczba
    nie odroznia raportu o czym innym od komunikatu, ktory nie nazywa NICZEGO.
    """
    if ("slad", root, szeroko) in _PAMIEC:
        return _PAMIEC[("slad", root, szeroko)]
    out = {k: [] for k in ("dotyczy", "nic_wspolnego", "bez_raportu",
                           "tylko_wszechobecne", "komunikat_nic_nie_nazywa",
                           "raport_nic_nie_nazywa", "rozne_nazwy")}
    teksty = komunikaty(root)
    for sha, _, pliki, tresc_raportow in strumien_diffow(root):
        komunikat = teksty.get(sha, "")
        if not zglasza_wykonana_kontrole(komunikat):
            continue
        if not any(SLAD_KONTROLI.search(p) for p in pliki):
            continue
        if not any(RAPORT_W_DIFFIE.match(p) for p in pliki):
            out["bez_raportu"].append(sha)
            continue
        w_raporcie = nazwy_modulow_i_zapadek(tresc_raportow)
        w_komunikacie = nazwy_modulow_i_zapadek(
            komunikat if szeroko else okno_wokol_kontroli(komunikat))
        wspolne = w_komunikacie & w_raporcie
        if wspolne:
            out["dotyczy"].append(sha)
            if wspolne <= WSZECHOBECNE_NAZWY:
                out["tylko_wszechobecne"].append(sha)
        else:
            out["nic_wspolnego"].append(sha)
            if not w_komunikacie:
                out["komunikat_nic_nie_nazywa"].append(sha)
            elif not w_raporcie:
                out["raport_nic_nie_nazywa"].append(sha)
            else:
                out["rozne_nazwy"].append(sha)
    _PAMIEC[("slad", root, szeroko)] = out
    return out


def cztery_populacje(root):
    """Dwie pary „zgloszone" wobec „widoczne" — i adresy commitow kazdej z nich."""
    if ("cztery", root) in _PAMIEC:
        return _PAMIEC[("cztery", root)]
    zglasza_zapadke, zglasza_i_widac = [], []
    zglasza_kontrole, zglasza_kontrole_ze_sladem = [], []
    widoczne_bez_zgloszonego = []
    teksty = komunikaty(root)
    for sha, w_diffie, pliki, _ in strumien_diffow(root):
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
    _PAMIEC[("cztery", root)] = {
        "zglasza_zapadke": zglasza_zapadke,
        "zglasza_i_widac": zglasza_i_widac,
        "zglasza_kontrole": zglasza_kontrole,
        "zglasza_kontrole_ze_sladem": zglasza_kontrole_ze_sladem,
        "widoczne_bez_zgloszonego": widoczne_bez_zgloszonego,
    }
    return _PAMIEC[("cztery", root)]


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


def test_trzy_klasy_sladu_ktorych_zadalo_pole_wyjscie_6D283():
    """**Slad kontroli wobec kontroli, ktorej slad dotyczy — trzy klasy z historii.**

    Podlogi, a nie rownosci, z tego samego powodu co przy czterech populacjach
    wyzej: commitow tylko przybywa. Suma trzech klas ma sie rownac populacji
    `zglasza kontrole ze sladem`, bo klasy sa jej PODZIALEM — gdyby sie nie
    rownala, sito czytaloby dwie rozne populacje i zadna liczba nizej nie
    mowilaby o tej, o ktorej mysli czytajacy.
    """
    wasko = klasy_sladu(ROOT)
    szeroko = klasy_sladu(ROOT, szeroko=True)
    assert len(wasko["dotyczy"]) >= MIN_SLAD_DOTYCZY_WASKO, (
        "commitow, ktorych raport wymienia nazwe z okna kontroli, jest %d przy "
        "podlodze %d — czytnik oslepl albo historia zostala przepisana"
        % (len(wasko["dotyczy"]), MIN_SLAD_DOTYCZY_WASKO))
    assert len(szeroko["dotyczy"]) >= MIN_SLAD_DOTYCZY_SZEROKO, (
        "wariant szeroki daje %d przy podlodze %d"
        % (len(szeroko["dotyczy"]), MIN_SLAD_DOTYCZY_SZEROKO))
    assert len(wasko["bez_raportu"]) >= MIN_SLAD_BEZ_RAPORTU, (
        "commitow ze sladem, ktore raportu nie dopisuja, jest %d przy podlodze %d"
        % (len(wasko["bez_raportu"]), MIN_SLAD_BEZ_RAPORTU))
    for etykieta, klasy in (("waski", wasko), ("szeroki", szeroko)):
        suma = (len(klasy["dotyczy"]) + len(klasy["nic_wspolnego"])
                + len(klasy["bez_raportu"]))
        populacja = len(cztery_populacje(ROOT)["zglasza_kontrole_ze_sladem"])
        assert suma == populacja, (
            "wariant %s: trzy klasy daja %d, a populacja ze sladem ma %d — "
            "podzial przestal byc podzialem" % (etykieta, suma, populacja))
    assert len(szeroko["dotyczy"]) > len(wasko["dotyczy"]), (
        "wariant szeroki daje %d, a waski %d — sito przestalo rozrozniac nazwe "
        "stojaca PRZY kontroli od nazwy stojacej gdziekolwiek w komunikacie"
        % (len(szeroko["dotyczy"]), len(wasko["dotyczy"])))


def test_raport_o_czym_INNYM_wypada_z_klasy_dotyczy():
    """**Kontrola negatywna zaciesnienia, na commicie z drzewa.**

    Ten commit ma slad wedle kryterium dzisiejszego — dopisuje raport. Raport mowi
    o czym innym niz okno kontroli w jego komunikacie, wiec z klasy `dotyczy` ma
    wypasc. Bez tej polowy zaciesnienie nie jest zaciesnieniem, tylko druga nazwa
    tego samego sita.
    """
    klucz = COMMIT_SLAD_O_CZYM_INNYM[:7]
    ze_sladem = {s[:7] for s in cztery_populacje(ROOT)["zglasza_kontrole_ze_sladem"]}
    assert klucz in ze_sladem, (
        "commit %s wypadl z populacji ze sladem — przypadek przestal byc tym, "
        "czym byl, wiec zamien go na inny ZYWY i powiedz o tym" % klucz)
    for etykieta, szeroko in (("waski", False), ("szeroki", True)):
        klasy = klasy_sladu(ROOT, szeroko=szeroko)
        assert klucz not in {s[:7] for s in klasy["dotyczy"]}, (
            "wariant %s: commit %s stoi w klasie `dotyczy`, a jego raport nie "
            "wymienia ani jednej nazwy z jego komunikatu" % (etykieta, klucz))
        assert klucz in {s[:7] for s in klasy["rozne_nazwy"]}, (
            "wariant %s: commit %s nie trafil do `rozne_nazwy`, a obie strony "
            "nazwy maja — tylko inne" % (etykieta, klucz))


def test_raport_o_TEJ_SAMEJ_kontroli_w_klasie_dotyczy_ZOSTAJE():
    """**Kontrola przyrzadu: zaciesnienie ma odsiewac, a nie kasowac klase.**

    Sito, ktore wyrzuca takze commit z nazwa wspolna, daje liczbe mala z powodu,
    o ktorym nic nie mowi. Zgodnosc tego commita nie opiera sie przy tym na
    nazwach wszechobecnych i to jest tu sprawdzone osobno.
    """
    klucz = COMMIT_SLAD_TEJ_SAMEJ[:7]
    klasy = klasy_sladu(ROOT)
    assert klucz in {s[:7] for s in klasy["dotyczy"]}, (
        "commit %s wypadl z klasy `dotyczy`, a jego raport wymienia te sama "
        "zapadke co okno kontroli w komunikacie" % klucz)
    assert klucz not in {s[:7] for s in klasy["tylko_wszechobecne"]}, (
        "zgodnosc commita %s opiera sie wylacznie na nazwach wszechobecnych — "
        "przypadek przestal byc kontrola przyrzadu" % klucz)


def test_zgodnosc_na_samych_nazwach_wszechobecnych_jest_liczona_OSOBNO():
    """**Klasa `dotyczy` nie jest jednorodna i liczba sama tego nie powie.**

    `MIN_REPORTS` podnosi kazdy commit dopisujacy raport, a `test_all.py` stoi
    w kazdym poleceniu weryfikacji. Gdyby takich commitow bylo zero, znaczyloby to,
    ze podzbior przestal byc czytany; gdyby bylo ich tyle, co calej klasy —
    ze klasa nie mowi o niczym poza nimi.
    """
    klasy = klasy_sladu(ROOT)
    ile, cala = len(klasy["tylko_wszechobecne"]), len(klasy["dotyczy"])
    assert 0 < ile < cala, (
        "commitow zgodnych wylacznie przez nazwy wszechobecne jest %d przy klasie "
        "`dotyczy` liczacej %d — podzbior przestal byc podzbiorem wlasciwym"
        % (ile, cala))


def test_komunikaty_czytaja_root_KTORY_DOSTALY():
    """**Argument `root` byl ignorowany i zadna liczba by tego nie pokazala.**

    `komunikaty` brala sciezke z modulowego `ROOT` niezaleznie od argumentu, wiec
    czytana z innego drzewa oddawala komunikaty drzewa TEGO modulu — przy diffach
    tamtego. Kontrola jest tania i nie wymaga drugiego repozytorium: katalog bez
    `.git` ma sprawic, ze `git log` padnie. Zwrocenie czegokolwiek znaczy, ze
    czytnik poszedl gdzie indziej niz mu kazano.
    """
    with tempfile.TemporaryDirectory() as katalog:
        wynik = {}
        try:
            wynik = komunikaty(katalog)
            padlo = False
        except subprocess.CalledProcessError:
            padlo = True
        assert padlo, (
            "komunikaty(katalog bez repozytorium) zwrocily %d komunikatow — "
            "argument `root` jest ignorowany, a czytnik czyta drzewo wlasnego "
            "modulu" % len(wynik))


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
