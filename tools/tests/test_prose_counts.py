"""Liczby wpisane w PROZĘ obok bramki są porównywane z tym, co bramka mierzy.

**Skąd ta pozycja.** Audyt z 12.09.2026 znalazł dwa zdania nieprawdziwe, oba
stojące bezpośrednio przy przyrządzie, który mierzy dokładnie tę samą rzecz:

* `test_tree_walks.py` opisywał rejestr jako „Trzydzieści osiem: 13 przybitych,
  3 częściowe, 21 WOLNYCH i 1 poza zasięgiem skanu", gdy `len(ZAPADKI)` dawało
  **42** przy rozkładzie 15 / 3 / 23 / 1;
* `test_all.py` mówił „przebieg bez argumentu robi to samo dla 120 modulow",
  gdy modułów było **123**.

**Nie znalazł ich żaden test i nie mógł.** Akapit w `test_tree_walks.py` sam
zapewnia, że „rozjechać się ta lista nie może, bo jest porównywana z drzewem
W OBIE STRONY" — i to prawda o LIŚCIE, a nieprawda o ZDANIU nad nią. Bramka
porównywała słownik z drzewem, więc zdanie o słowniku leżało poza jej zasięgiem:
ten sam kształt, który projekt tropi od 6.D27, tylko o piętro wyżej.

**Dlaczego samo przeliczenie by nie wystarczyło.** Przepisanie „38" na „42"
naprawia dzisiaj i pozwala rozjechać się jutro — a rozjechało się już raz,
niezauważone przez 1 dzień i 4 zapadki. Liczba w prozie potrzebuje tego samego,
co liczba w kodzie: kogoś, kto ją porównuje.

**Cyfry, nie słowa, i obejście jest GŁOŚNE, a nie zakazane.** Dawne zdanie pisało
sumę słownie („Trzydzieści osiem"), a rozbicie cyframi — a zapis słowny to dokładnie
to obejście, które 6.D108 opisało przy `test_report_claims.py`: liczba przestaje być
widoczna dla czytnika, zostając widoczną dla człowieka. Deklaracja zapisana słownie
nie jest jednak przez tę bramkę PRZEPUSZCZANA, tylko NIEWIDZIANA — a dolne ostrze
na czytnik zamienia niewidzenie w czerwone „trafień: 0". Pilnuje tego kontrola
z wejściem syntetycznym, nie skan po słowach: skan zapalałby się na akapitach,
które CYTUJĄ dawne brzmienie, czyli karałby za opisanie przeszłości, a projekt
wymaga tego opisu w każdym przepisanym akapicie.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))

import test_tree_walks as TW

#: Zdanie o rejestrze zapadek. Cztery liczby: razem, przybite, częściowe, wolne.
#: Ostatnia (poza skanem) stoi w tym samym zdaniu i też jest czytana.
#:
#: **Kształt przepisany 15.09.2026 (6.D218), a nie dopisany obok.** Do tego dnia wzorzec
#: brzmiał `(\d+)\s+zapadek:\s*\*\*(\d+)\s+przybitych,…(\d+)\s+WOLNE\s+i…`,
#: czyli **wymuszał cztery formy gramatyczne bez względu na liczebnik przed nimi**.
#: Zmierzone na całej historii rejestru: zdanie było błędne przy KAŻDEJ wartości —
#: 46/25, 48/27, 49/28, 50/29, 51/30 żądały „WOLNYCH" zamiast „WOLNE", a przy 54/33 błąd
#: przeskoczył o słowo, bo „WOLNE" po 33 jest już poprawne, a „54 zapadek" po 54 nie.
#: Dziś liczba stoi PO etykiecie, więc przypadek rządzony jest dwukropkiem, a nie
#: liczebnikiem, i wzorzec nie wymusza **żadnej** formy. Przechwyceń jest nadal pięć.
WZORZEC_ZAPADEK = re.compile(
    r"Zapadek:\s*(\d+)\.\s*\*\*Przybitych:\s*(\d+),\s*częściowych:\s*(\d+),\s*"
    r"WOLNYCH:\s*(\d+),\s*poza\s+zasięgiem\s+skanu:\s*(\d+)\.\*\*")

#: Zdanie o liczbie modułów zestawu.
WZORZEC_MODULOW = re.compile(r"robi to samo dla (\d+) modulow")

#: Zdanie o liczbie pomocników parsujących liczby (`test_runner_number_parsing.py`).
#: **Zapisane SŁOWNIE — i to jest cały powód, dla którego ta deklaracja tu doszła**
#: (6.D203). Znalazł ją skan liczebników opisany niżej; do 14.09.2026 nie porównywało
#: jej z niczym ani jedno wywołanie, a `len(POMOCNIKI)` nie było przybite w drzewie
#: nigdzie. Czwarty pomocnik dopisany do krotki zostawiłby to zdanie nieprawdziwym
#: i nikt by się o tym nie dowiedział — dokładnie ten kształt, który ten moduł łapie.
#:
#: **Kształt przepisany 15.09.2026 (6.D218).** Do tego dnia wzorzec brzmiał
#: `([A-Za-z…]+) pomocniki, ktore maja byc JEDYNA droga` i wymuszał formę `pomocniki` —
#: poprawną po „trzy", ale **błędną po każdym liczebniku spoza 2–4**, czyli po każdym,
#: do którego ta krotka mogłaby urosnąć. Dziś liczebnik stoi PO etykiecie.
WZORZEC_POMOCNIKOW = re.compile(
    r"Pomocnikow, ktore maja byc JEDYNA droga wartosci opcji do liczby: "
    r"([^\W\d_]+)")

#: Liczebniki potrzebne do PRZECZYTANIA deklaracji, a nie do SKANOWANIA prozy —
#: i ta granica jest treścią, a nie ostrożnością (6.D203, pomiar niżej). Mapa jest
#: wołana wyłącznie przez wzorce zadeklarowane w tym module, czyli w miejscach,
#: o których wiadomo, że są deklaracjami. Puszczona po całej prozie dałaby
#: 1216 trafień przy 4 deklaracjach — patrz `test_skan_liczebnikow_JAKO_BRAMKA…`.
#: **Odmiana JEST w mapie i to nie jest ozdoba.** Deklaracje stoją w mianowniku,
#: więc do samego czytania wystarczyłoby dwadzieścia kluczy — ale ta sama mapa karmi
#: skan z pomiaru 6.D203, a proza tego drzewa pisze „jednego", „dwóch", „trzech"
#: częściej niż formy podstawowe. Zmierzone tym samym skanem: mapa z 23 kluczami
#: (same mianowniki) daje 774 trafienia, mapa z 92 — 1216. Wąska zaniżyłaby liczbę,
#: na której stoi werdykt, o 36 %.
LICZEBNIKI = {
    "jeden": 1, "jedna": 1, "jedno": 1, "jednego": 1, "jednej": 1, "jednym": 1,
    "jedną": 1, "jednemu": 1,
    "dwa": 2, "dwie": 2, "dwóch": 2, "dwoma": 2, "dwiema": 2, "dwu": 2, "dwoje": 2,
    "trzy": 3, "trzech": 3, "trzema": 3, "troje": 3,
    "cztery": 4, "czterech": 4, "czterema": 4, "czworo": 4,
    "pięć": 5, "pięciu": 5, "pięcioma": 5, "pięcioro": 5,
    "sześć": 6, "sześciu": 6, "sześcioma": 6, "sześcioro": 6,
    "siedem": 7, "siedmiu": 7, "siedmioma": 7, "siedmioro": 7,
    "osiem": 8, "ośmiu": 8, "ośmioma": 8, "ośmioro": 8,
    "dziewięć": 9, "dziewięciu": 9, "dziewięcioma": 9,
    "dziesięć": 10, "dziesięciu": 10, "dziesięcioma": 10,
    "jedenaście": 11, "jedenastu": 11, "dwanaście": 12, "dwunastu": 12,
    "trzynaście": 13, "trzynastu": 13, "czternaście": 14, "czternastu": 14,
    "piętnaście": 15, "piętnastu": 15, "szesnaście": 16, "szesnastu": 16,
    "siedemnaście": 17, "siedemnastu": 17, "osiemnaście": 18, "osiemnastu": 18,
    "dziewiętnaście": 19, "dziewiętnastu": 19,
    "dwadzieścia": 20, "dwudziestu": 20, "trzydzieści": 30, "trzydziestu": 30,
    "czterdzieści": 40, "czterdziestu": 40, "pięćdziesiąt": 50, "pięćdziesięciu": 50,
    "sześćdziesiąt": 60, "sześćdziesięciu": 60,
    "siedemdziesiąt": 70, "siedemdziesięciu": 70,
    "osiemdziesiąt": 80, "osiemdziesięciu": 80,
    "dziewięćdziesiąt": 90, "dziewięćdziesięciu": 90,
    "sto": 100, "stu": 100, "dwieście": 200, "dwustu": 200,
    "trzysta": 300, "trzystu": 300, "czterysta": 400, "czterystu": 400,
    "pięćset": 500, "pięciuset": 500,
    "tysiąc": 1000, "tysiąca": 1000, "tysięcy": 1000,
}

#: Ile DEKLARACJI czyta dziś ta bramka. Zapadka w JEDNĄ stronę: deklaracja raz objęta
#: czytaniem nie ma prawa z niego wypaść, bo wypadnięcie jest bezgłośne — zdanie
#: zostaje w pliku i wygląda tak samo jak przedtem. 2 -> 3 (14.09.2026, 6.D203).
#:
#: **Ta liczba mówi też, JAK MAŁE jest pokrycie, i po to tu stoi drugi raz:**
#: zapadek w rejestrze `test_tree_walks.ZAPADKI` jest 45, a deklaracji czytanych —
#: 3. Reszta prozy przy zapadkach nie jest pilnowana przez nic i **nie da się jej
#: pilnować skanem** (pomiar niżej); da się wyłącznie dopisywać wzorce po jednym.
DEKLARACJI_POD_BRAMKA = 3


def _zrodlo(nazwa):
    with open(os.path.join(ROOT, "tools", "tests", nazwa), encoding="utf-8") as f:
        return f.read()


def _moduly_zestawu():
    """Ile modułów testowych leży pod `tools/tests/` — ta sama populacja,
    o której mówi zdanie w `test_all.py`."""
    katalog = os.path.join(ROOT, "tools", "tests")
    return len([n for n in os.listdir(katalog)
                if n.startswith("test_") and n.endswith(".py")])


def _rozklad_rejestru():
    razem = len(TW.ZAPADKI)
    klasy = {TW.PRZYBITA: 0, TW.CZESCIOWA: 0, TW.WOLNA: 0, TW.POZA_SKANEM: 0}
    for klasa, _modul in TW.ZAPADKI.values():
        klasy[klasa] += 1
    return razem, klasy


def test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem():
    """Cztery liczby z prozy kontra cztery policzone ze słownika."""
    zrodlo = _zrodlo("test_tree_walks.py")
    trafienia = WZORZEC_ZAPADEK.findall(zrodlo)

    # Dolne ostrze na SAM CZYTNIK: przeredagowane zdanie ma paść głośno,
    # a nie przejść przez pustą listę bez ani jednego porównania (6.D27).
    assert len(trafienia) == 1, (
        "zdanie o rejestrze zapadek nie zostało znalezione (trafień: %d) — "
        "albo je przeredagowano, albo wzorzec zgnił; bramka nie ma czego "
        "porównać" % len(trafienia))

    razem, przybite, czesciowe, wolne, poza = (int(x) for x in trafienia[0])
    zm_razem, zm_klasy = _rozklad_rejestru()

    assert razem == zm_razem, (
        "proza mówi o %d zapadkach, a rejestr ma %d" % (razem, zm_razem))
    assert przybite == zm_klasy[TW.PRZYBITA], (
        "proza: %d przybitych, rejestr: %d" % (przybite, zm_klasy[TW.PRZYBITA]))
    assert czesciowe == zm_klasy[TW.CZESCIOWA], (
        "proza: %d częściowe, rejestr: %d" % (czesciowe, zm_klasy[TW.CZESCIOWA]))
    assert wolne == zm_klasy[TW.WOLNA], (
        "proza: %d wolnych, rejestr: %d" % (wolne, zm_klasy[TW.WOLNA]))
    assert poza == zm_klasy[TW.POZA_SKANEM], (
        "proza: %d poza skanem, rejestr: %d" % (poza, zm_klasy[TW.POZA_SKANEM]))

    # Suma klas ma się równać całości — inaczej zdanie może być prawdziwe
    # w każdym członie i nadal gubić zapadkę między klasami.
    assert przybite + czesciowe + wolne + poza == razem, (
        "człony zdania nie sumują się do jego własnej sumy: %d+%d+%d+%d != %d"
        % (przybite, czesciowe, wolne, poza, razem))


def test_zdanie_o_liczbie_modulow_zgadza_sie_z_katalogiem():
    """Liczba modułów z prozy `test_all.py` kontra `tools/tests/`."""
    zrodlo = _zrodlo("test_all.py")
    trafienia = WZORZEC_MODULOW.findall(zrodlo)

    assert len(trafienia) == 1, (
        "zdanie o liczbie modułów nie zostało znalezione (trafień: %d)"
        % len(trafienia))

    zadeklarowane = int(trafienia[0])
    zmierzone = _moduly_zestawu()
    assert zadeklarowane == zmierzone, (
        "proza mówi o %d modułach, a pod `tools/tests/` leży %d"
        % (zadeklarowane, zmierzone))


def test_czytnik_nie_widzi_deklaracji_zapisanej_slownie_i_mowi_o_tym_glosno():
    """Zapis słowny jest obejściem tej bramki — kontrola przyrządu, wejście syntetyczne.

    **Dlaczego nie skan całego pliku.** Pierwsza wersja tego testu szukała słów
    („Trzydzieści", „czterdzieści dwie") w CAŁYM `test_tree_walks.py` i zapaliła
    się natychmiast — na akapicie, który CYTUJE dawne brzmienie, żeby wyjaśnić,
    co się zmieniło. Cytat historyczny wygląda dokładnie jak deklaracja, i jest to
    ta sama obserwacja, którą 6.D108 zrobiło dla raportów: kształtu nie ma.
    Skan po słowach kazałby więc nie opisywać przeszłości, czyli psułby to,
    czego projekt wymaga w każdym przepisanym akapicie.

    **Co zostaje zmierzone zamiast tego.** Że obejście nie jest ciche: deklaracja
    zapisana słownie nie jest przez `WZORZEC_ZAPADEK` widziana wcale, więc
    `test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem` pada na dolnym ostrzu
    („trafień: 0"), a nie przechodzi. Bramka nie da się obejść zapisem słownym —
    da się nią najwyżej zapalić.
    """
    # Obie próbki noszą KSZTAŁT DZISIEJSZY (6.D218: liczba po etykiecie). Próbka
    # w starym kształcie mierzyłaby od 15.09.2026 to, czy wzorzec widzi zdanie, którego
    # w drzewie już nie ma — czyli nic.
    slownie = ("#: Zapadek: trzydzieści osiem. **Przybitych: 13, częściowych: 3,\n"
               "#: WOLNYCH: 21, poza zasięgiem skanu: 1.**")
    assert WZORZEC_ZAPADEK.findall(slownie) == [], (
        "czytnik zobaczył deklarację zapisaną słownie — wtedy zapis słowny "
        "przestaje być głośnym brakiem, a staje się cichym obejściem")

    cyframi = ("#: Zapadek: 42. **Przybitych: 15, częściowych: 3, WOLNYCH: 23, "
               "poza zasięgiem skanu: 1.**")
    assert WZORZEC_ZAPADEK.findall(cyframi) == [("42", "15", "3", "23", "1")], (
        "czytnik przestał widzieć deklarację zapisaną cyframi — kontrola wyżej "
        "mierzyłaby wtedy nie obejście, tylko własną ślepotę: %s"
        % WZORZEC_ZAPADEK.findall(cyframi))

    # **Trzecia próbka jest nowa (6.D218) i to ona pilnuje ODPORNOŚCI KSZTAŁTU.**
    # Stary wzorzec miał formy wpisane na sztywno, więc zdanie zapisane POPRAWNĄ
    # polszczyzną przy innym liczebniku wypadało spod bramki — dokładnie to, co
    # ta pozycja naprawia. Dziś cztery różne liczebniki, wymagające po polsku
    # czterech różnych form, czyta ten sam wzorzec bez zmiany ani jednego słowa.
    for liczba in ("1", "2", "5", "22"):
        probka = ("#: Zapadek: %s. **Przybitych: %s, częściowych: %s, WOLNYCH: %s, "
                  "poza zasięgiem skanu: %s.**" % ((liczba,) * 5))
        assert WZORZEC_ZAPADEK.findall(probka) == [((liczba,) * 5)], (
            "wzorzec nie przeczytał zdania z liczebnikiem `%s` — kształt znów zależy "
            "od liczby, a po polsku forma po liczebniku zmienia się z jego końcówką "
            "(6.D218)" % liczba)


def test_zdanie_o_liczbie_pomocnikow_zgadza_sie_z_krotka():
    """Deklaracja zapisana SŁOWNIE, czytana przez mapę liczebników — 6.D203.

    To jest jedyna znaleziona w drzewie deklaracja słowna, która opisuje wielkość
    **żywą** i której nie porównywało z niczym ani jedno wywołanie. Druga znaleziona
    (`test_platform_length_in_pipeline.py`: „04.09.2026 wywołań są dwa") jest
    DATOWANA, czyli opisuje pomiar z konkretnego dnia i starzeć się nie może.
    """
    import test_runner_number_parsing as RNP

    zrodlo = _zrodlo("test_runner_number_parsing.py")
    trafienia = WZORZEC_POMOCNIKOW.findall(zrodlo)

    # Dolne ostrze na SAM CZYTNIK — to samo, co przy dwóch deklaracjach wyżej.
    assert len(trafienia) == 1, (
        "zdanie o liczbie pomocników nie zostało znalezione (trafień: %d) — "
        "albo je przeredagowano, albo wzorzec zgnił" % len(trafienia))

    # WIELKOŚĆ LITERY ZDEJMOWANA TUTAJ, a nie dopisywana do mapy drugim kluczem.
    # **Powód jest dziś inny niż w dniu, w którym to napisano, i dlatego jest przepisany
    # (6.D218).** Stało tu, że „deklaracja zaczyna zdanie, więc stoi z wielkiej
    # (»Trzy pomocniki«)" — po zmianie kształtu zdania liczebnik stoi w ŚRODKU i z małej.
    # `.lower()` zostaje mimo to: mapa ma służyć też skanowi czytającemu środek zdania,
    # a dwa klucze na to samo słowo rozjechałyby się przy pierwszej edycji jednego z nich.
    # Zdjęcie wielkości litery jest więc odporne na OBA kształty, i to jest jego wartość.
    slowo = trafienia[0].lower()
    assert slowo in LICZEBNIKI, (
        "liczebnik `%s` nie jest w mapie — deklaracja przestałaby być czytana, "
        "a to jest dokładnie ten bezgłośny wypad, którego broni "
        "`DEKLARACJI_POD_BRAMKA`" % slowo)

    zadeklarowane = LICZEBNIKI[slowo]
    assert zadeklarowane == len(RNP.POMOCNIKI), (
        "proza mówi o %d pomocnikach (`%s`), a krotka ma %d: %s"
        % (zadeklarowane, slowo, len(RNP.POMOCNIKI), ", ".join(RNP.POMOCNIKI)))


def test_ile_deklaracji_czyta_ta_bramka_i_ile_jest_zapadek():
    """Pokrycie bramki jest LICZBĄ w drzewie, a nie wrażeniem — 6.D203.

    Bez tej asercji zdanie „bramka czyta trzy deklaracje" byłoby prozą przy zapadce,
    czyli dokładnie tym, czego ten moduł pilnuje u innych.
    """
    wzorce = [WZORZEC_ZAPADEK, WZORZEC_MODULOW, WZORZEC_POMOCNIKOW]

    assert len(wzorce) == DEKLARACJI_POD_BRAMKA, (
        "wzorców deklaracji jest %d, a zapadka mówi %d — deklaracja dopisana bez "
        "podniesienia tej liczby albo zdjęta bez jej obniżenia"
        % (len(wzorce), DEKLARACJI_POD_BRAMKA))

    # Druga połowa, i to ona jest tu treścią: pokrycie jest MAŁE i ma to być widać.
    assert DEKLARACJI_POD_BRAMKA < len(TW.ZAPADKI), (
        "bramka czyta %d deklaracji przy %d zapadkach — jeżeli liczby się zrównały, "
        "zdanie o małym pokryciu w opisie `DEKLARACJI_POD_BRAMKA` przestało być "
        "prawdziwe i ma zostać przepisane"
        % (DEKLARACJI_POD_BRAMKA, len(TW.ZAPADKI)))


#: Deklaracje SŁOWNE znalezione skanem liczebników w promieniu 2 wierszy od zapadki —
#: wypisane Z NAZWY, nie policzone (6.D131: zbiór przeżywa edycję prozy, liczba nie).
#: Obie są PRAWDZIWE na dziś; pierwsza jest datowana, druga żywa i to ona dostała
#: wzorzec wyżej.
DEKLARACJE_SLOWNE = (
    # DATOWANE — opisują pomiar z konkretnego dnia, więc zestarzeć się nie mogą.
    ("test_platform_length_in_pipeline.py", "04.09.2026 wywołań są dwa"),
    ("test_game_needle_specificity.py", "Zmierzone 07.09.2026: cztery"),
    # ŻYWA, ale powtarza deklarację pilnowaną gdzie indziej: próg z `CLAUDE.md` §8
    # czyta `test_backlog.prog_z_dokumentu`, też ze słowa, i porównuje go
    # z `MINIMUM_READY_ITEMS`. Ten komentarz jest jej echem, nie źródłem.
    ("test_backlog.py", "dwanaście pozycji to dolna granica doby pracy"),
    # ŻYWA I NIEPILNOWANA PRZEZ NIC — jedyna taka w drzewie; to ona dostała wzorzec.
    ("test_runner_number_parsing.py",
     "Pomocnikow, ktore maja byc JEDYNA droga wartosci opcji do liczby: trzy"),
)

#: Dolne ostrze na skan liczebników z pomiaru 6.D203. Zmierzone 14.09.2026 na prozie
#: 21 modułów niosących zapadkę: **1216** liczb słownych, z tego **23** w promieniu
#: 2 wierszy od definicji zapadki. Ostrze stoi nisko (900), bo liczba rusza się przy
#: KAŻDEJ edycji prozy w tych modułach — pilnuje tego, że skan nie oślepł, a nie tego,
#: ile dokładnie wynosi.
MINIMUM_LICZB_SLOWNYCH = 900


def _moduly_do_pomiaru():
    """Moduły niosące zapadkę, BEZ tego pliku — i to wyłączenie jest treścią.

    Ten moduł sam dostał zapadkę (`MINIMUM_LICZB_SLOWNYCH`), więc od 14.09.2026 wpada
    do populacji, którą mierzy. Bez wyłączenia liczba z pomiaru 6.D203 staje się
    **samozwrotna**: każde słowo dopisane do prozy TEGO pliku ją zmienia, a proza tego
    pliku opisuje właśnie ją. Zmierzone: z tym plikiem 1244 trafienia, bez niego 1216.
    Liczba, którą da się zmienić zdaniem o niej samej, nie jest pomiarem drzewa.
    """
    return sorted({modul for _klasa, modul in TW.ZAPADKI.values()
                   if modul != "test_prose_counts.py"})


def _liczby_slowne_w_prozie(modul):
    """Liczby słowne w PROZIE modułu: `{numer wiersza: [słowa]}`.

    Proza, czyli komentarze i napisy dokumentacyjne — kod jest pomijany przez sam
    `tokenize`, a nie przez wyrażenie regularne po nawiasach (rodzina 6.D27:
    przyrząd liczący własnym rozbiorem mówi o sobie).
    """
    import tokenize

    sciezka = os.path.join(ROOT, "tools", "tests", modul)
    if not os.path.exists(sciezka):
        return {}

    out = {}
    with open(sciezka, "rb") as f:
        try:
            tokeny = list(tokenize.tokenize(f.readline))
        except tokenize.TokenError:
            return {}

    poprzedni = None
    for token in tokeny:
        proza = None
        if token.type == tokenize.COMMENT:
            proza = [token.string]
        elif token.type == tokenize.STRING and poprzedni in (
                None, tokenize.INDENT, tokenize.DEDENT,
                tokenize.NEWLINE, tokenize.NL):
            proza = token.string.splitlines()
        if proza is not None:
            for i, wiersz in enumerate(proza):
                slowa = [w for w in re.findall(
                    r"[^\W\d_]+", wiersz)
                    if w.lower() in LICZEBNIKI]
                if slowa:
                    out.setdefault(token.start[0] + i, []).extend(slowa)
        if token.type != tokenize.NL:
            poprzedni = token.type
    return out


def test_skan_liczebnikow_JAKO_BRAMKA_jest_NIEMOZLIWY_i_to_jest_zmierzone():
    """Rozstrzygnięcie 6.D203: skanu liczebników postawić się NIE DA.

    Pole „Skończone, gdy" tej pozycji żąda dwóch liczb i werdyktu. Werdykt brzmi
    **nie da się**, a rozstrzygnęły go te liczby — zmierzone 14.09.2026 na prozie
    21 modułów niosących zapadkę z `test_tree_walks.ZAPADKI`:

    * liczb słownych w tej prozie razem: **1216**;
    * w promieniu 2 wierszy od definicji zapadki: **23**;
    * w promieniu 12 wierszy: **93**;
    * z tych 93 równych WARTOŚCI sąsiedniej zapadki: **9**, a deklaracjami są z nich
      **2** — reszta to zwykła proza, która ma pecha trafić w tę samą liczbę
      („lista rośnie w jedną stronę", „kupki byłyby dwie", „Zostało jedno i ma
      powód", „38 przy dwóch, 32 przy ośmiu");
    * z 1216 równych wartości JAKIEJKOLWIEK zapadki: **1192**, czyli 98 %, bo
      wartościami zapadek są między innymi 1, 2, 3, 4 i 5. Sito „liczba słowna
      równa wartości zapadki" zgłasza więc prawie całą prozę tego drzewa.

    **Werdykt nie zależy od promienia** i to też jest zmierzone: 2 wiersze dają 23
    trafień, 4 dają 38, 8 daje 65, 12 daje 93, 20 daje 143, 40 daje 227 — a liczba
    prawdziwych deklaracji stoi na **4** w całym drzewie, z czego **1** jest żywa
    i niepilnowana przez nic.

    **Czym ten skan JEST, skoro nie jest bramką.** Przyrządem TRIAŻU: zwęził 1216
    zdań do 25 do przeczytania ręką i znalazł wśród nich deklarację, której nie
    pilnowało nic (`POMOCNIKI` — `len()` tej krotki nie było przybite w drzewie
    nigdzie). Bramką zostaje to, co działa — WZORZEC na konkretną deklarację,
    z dolnym ostrzem na zero trafień. Dlatego ta pozycja kończy się trzecim wzorcem,
    a nie skanem po słowach.
    """
    moduly = _moduly_do_pomiaru()
    trafienia = 0
    for modul in moduly:
        for slowa in _liczby_slowne_w_prozie(modul).values():
            trafienia += len(slowa)

    # Dolne ostrze na SAM SKAN: przyrząd, który nie widzi nic, „udowodniłby"
    # brak fałszywych trafień zerem (6.D27).
    assert trafienia >= MINIMUM_LICZB_SLOWNYCH, (
        "skan liczebników znalazł %d liczb słownych w prozie %d modułów wobec "
        "zmierzonego dolnego ostrza %d — przyrząd oślepł i jego werdykt o fałszywych "
        "trafieniach nie znaczy nic" % (trafienia, len(moduly), MINIMUM_LICZB_SLOWNYCH))

    # Sedno: prawdziwych deklaracji jest GARŚĆ, a trafień tysiące.
    assert trafienia > 100 * len(DEKLARACJE_SLOWNE), (
        "trafień skanu (%d) przestało być o dwa rzędy wielkości więcej niż "
        "deklaracji (%d) — jeżeli proza tych modułów naprawdę tak zeszczuplała, "
        "rozstrzygnięcie 6.D203 wymaga przeliczenia, a nie przepisania"
        % (trafienia, len(DEKLARACJE_SLOWNE)))


def test_znalezione_deklaracje_slowne_nadal_stoja_w_drzewie():
    """Lista z 6.D203 nie ma prawa zgnić po cichu.

    Zdanie usunięte z drzewa zostawiłoby wpis, który opisuje nieistniejący tekst —
    a wtedy „znaleźliśmy dwie deklaracje słowne" byłoby zdaniem o przeszłości
    udającym zdanie o dziś.
    """
    for modul, zdanie in DEKLARACJE_SLOWNE:
        zrodlo = _zrodlo(modul)
        assert zdanie in zrodlo, (
            "deklaracja słowna znaleziona przy 6.D203 zniknęła z `%s`: %s — "
            "zdejmij wpis albo przywróć zdanie" % (modul, zdanie))


# --- 6.D207: CZY DA SIE ODSIAC ZDANIE DEKLARUJACE POMIAR, POD KTORYM NIC NIE STOI ----
#
# **ODPOWIEDZ: NIE DA SIE, i nie jest to ostroznosc — sa to DWIE liczby.**
#
# Pozycja wyszla od zdania „Innych list pomiarow w drzewie NIE MA, i to jest zmierzone,
# nie zalozone", ktore stalo w docstringu
# `test_zaden_wpis_nie_niesie_rangi_OTWARTEJ_w_tej_liscie` **przy zerze linii kodu
# wykonujacych tamten skan** — a mimo to przeszlo pelny zestaw, przeglad i scalenie.
#
# Zmierzone 14.09.2026 na `3d1223b`:
#
#     docstringow w `tools/tests/`                                     2489
#     zdan DEKLARUJACYCH pomiar                                          29
#     z nich zdan o CUDZYM pomiarze (wzorzec „6.Dxxx zmierzylo")           0
#     deklaracji w docstringu MODULU albo KLASY (brak ciala do sprawdzenia) 4
#     funkcji POMOCNICZYCH z deklaracja i ZEREM asercji                    5
#     funkcji TESTOWYCH z deklaracja                                      19
#     z nich testowych z deklaracja i ZEREM asercji                        0
#
# **TRAFIENIA FALSZYWE: 5 na 5, czyli 100 %.** Jedyne sito, ktore da sie napisac
# mechanicznie — „docstring deklaruje pomiar, a w ciele nie ma ani jednej asercji" —
# zglasza wylacznie POMOCNIKI (`pokrycie_w_celach`, `wiersze_starego_bajtkodu`,
# `documents`, `_dziennik_testu`, `cpu_dzieci`). Pomocnik bez asercji jest poprawny
# z definicji: liczy i zwraca, a sprawdza go wolajacy. Bramka swiecaca na poprawnym
# tekscie zostaje wylaczona, nie poprawiona (6.D27).
#
# **TRAFIENIE POMINIETE: 1 na 1, i to jest liczba wazniejsza.** Sito jest slepe na
# przypadek, dla ktorego pozycje napisano. W commicie, ktory to zdanie WPROWADZIL
# (`a5e9ff0`, 6.D163), funkcja miala **6 asercji** — sito powiedzialoby o niej
# „zielona" dokladnie tak samo, jak mowi dzis, gdy zdanie jest juz sprawdzane
# (6.D193 dolozylo skan). **Ten sam werdykt na wejsciu poprawnym i na wadliwym**
# znaczy, ze przyrzad nie mierzy tej roznicy — rodzina 6.D75.
#
# **TRAFIEN PRAWDZIWYCH W DZISIEJSZYM DRZEWIE JEST ZERO, i to jest trzecia liczba.**
# Jedyne znane w historii tego repozytorium naprawilo 6.D193: tamten docstring mowi dzis
# „od 6.D193 jest to SPRAWDZANE, a nie przeczytane" i deklaracji pomiaru juz nie niesie.
# Sita nie da sie wiec sprawdzic na zbiorze prawdziwych trafien, bo taki zbior jest
# pusty — stad para syntetyczna w bramce nizej i liczba wzieta z commita, ktory usterke
# WPROWADZIL, a nie z drzewa, ktore ja juz zabralo.
#
# Dlaczego inaczej sie nie da: zdanie deklaruje, ze ZMIERZONO KONKRETNA RZECZ,
# a asercja obok mierzy JAKAS rzecz. Zwiazanie jednego z drugim jest rozbiorem
# znaczenia zdania, a nie skladni — czyli §8 `CLAUDE.md`, nie praca dla wzorca.
#
# **CO WIEC ZOSTAJE W DRZEWIE:** populacja i jej rozklad, zeby liczby, na ktorych ten
# werdykt stoi, nie zestarzaly sie w ciszy, oraz ZBIOR pieciu pomocnikow — bo to on,
# a nie liczba 5, rozstrzyga o „100 % trafien falszywych".

#: Wzorzec zdania DEKLARUJACEGO wlasny pomiar. Nie jest to sito po slowie „zmierzone":
#: tym slowem zaczyna sie w tym drzewie niemal kazde pole „Skad" (6.D196 zmierzylo, ze
#: `HISTORICAL_MARKERS` z nim w srodku jest spelnione zawsze). Lapane sa ZWROTY, ktore
#: stawiaja pomiar w opozycji do zalozenia albo nazywaja jego wykonanie.
WZORZEC_DEKLARACJI_POMIARU = re.compile(
    r"zmierzone,\s*(?:a\s*)?nie\s+(?:zało|zalo|wywnio|przewid)"
    r"|to\s+jest\s+zmierzone|jest\s+to\s+zmierzone"
    r"|policzon[aeo]\s+ze\s+źródeł|policzon[aeo]\s+na\s+drzewie"
    r"|skan\s+znalazł|sprawdzone\s+wykonaniem|zmierzone\s+wykonaniem"
    r"|odtworzone\s+celowo",
    re.IGNORECASE)

#: Podloga na liczbe deklaracji. PODLOGA, nie rownosc: deklaracji przybywa z kazda
#: pozycja, ktora cos zmierzy, czyli przy pracy poprawnej. Broni przed jedna rzecza —
#: wzorcem, ktory zgnil i odpowiada zerem tak samo jak wzorzec dzialajacy (6.D27).
#: Zmierzone 14.09.2026: 29 zdan w 2489 docstringach.
MIN_DEKLARACJI_POMIARU = 22

#: Funkcje, ktore sito „deklaracja bez asercji" zglasza — WSZYSTKIE POMOCNICZE,
#: czyli wszystkie falszywe. Zbior, nie liczba (6.D131): to on niesie zdanie
#: „100 % trafien falszywych", a liczba 5 jest tylko jego dlugoscia.
DEKLARACJE_BEZ_ASERCJI = {
    ("tools/tests/mutation_sweep.py", "pokrycie_w_celach"),
    ("tools/tests/mutation_sweep.py", "wiersze_starego_bajtkodu"),
    ("tools/tests/test_docs_ci_claims.py", "documents"),
    ("tools/tests/test_mutation_sweep.py", "_dziennik_testu"),
    ("tools/tests/test_suite_runtime_budget.py", "cpu_dzieci"),
}

#: Funkcja, na ktorej zmierzono TRAFIENIE POMINIETE, i jej liczba asercji w commicie
#: `a5e9ff0`, ktory wprowadzil do jej docstringu zdanie niesprawdzane niczym.
FUNKCJA_TRAFIENIA_POMINIETEGO = (
    "tools/tests/test_suite_runtime_budget.py",
    "test_zaden_wpis_nie_niesie_rangi_OTWARTEJ_w_tej_liscie")
ASERCJI_W_COMMICIE_a5e9ff0 = 6


def _funkcje_z_deklaracja_pomiaru():
    """`[(plik, nazwa, asercji, czy_test)]` — funkcje pod `tools/tests/`, ktorych
    docstring deklaruje pomiar. Przez `tree_walk.walk`, jak kazdy skan w tym projekcie.
    """
    import ast
    import tree_walk as tw

    out = []
    for baza, _kat, pliki in tw.walk(os.path.join(ROOT, "tools", "tests")):
        for plik in sorted(pliki):
            if not plik.endswith(".py"):
                continue
            sciezka = os.path.join(baza, plik)
            with open(sciezka, encoding="utf-8", errors="replace") as uchwyt:
                try:
                    drzewo = ast.parse(uchwyt.read())
                except SyntaxError:
                    continue
            for wezel in ast.walk(drzewo):
                if not isinstance(wezel, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                doc = ast.get_docstring(wezel) or ""
                if not WZORZEC_DEKLARACJI_POMIARU.search(doc):
                    continue
                asercji = sum(1 for w in ast.walk(wezel) if isinstance(w, ast.Assert))
                out.append((os.path.relpath(sciezka, ROOT), wezel.name, asercji,
                            wezel.name.startswith("test_")))
    return out


def test_sito_deklaracji_bez_asercji_zglasza_SAME_POMOCNIKI():
    """Trafienia falszywe: 5 na 5 — pierwsza z dwoch liczb, ktorych zadalo pole „Wyjscie".

    Pomocnik bez asercji jest poprawny z definicji: liczy i zwraca, a sprawdza go
    wolajacy. Sito, ktore zglasza wylacznie ich, nie zglasza ani jednej usterki.
    """
    znalezione = _funkcje_z_deklaracja_pomiaru()

    assert len(znalezione) >= MIN_DEKLARACJI_POMIARU, (
        "funkcji z deklaracja pomiaru w docstringu jest %d przy podlodze %d — wzorzec "
        "zgnil albo drzewo sie skurczylo, a zero odpowiada tak samo jak wzorzec "
        "dzialajacy" % (len(znalezione), MIN_DEKLARACJI_POMIARU))

    bez_asercji = {(plik, nazwa) for plik, nazwa, asercji, _t in znalezione if asercji == 0}
    assert bez_asercji == DEKLARACJE_BEZ_ASERCJI, (
        "sito „deklaracja bez asercji\" zglasza dzis %s, a wymienione sa %s — jesli "
        "doszla funkcja TESTOWA, werdykt 6.D207 („100 %% trafien falszywych\") "
        "przestal byc prawdziwy i trzeba go przeliczyc"
        % (sorted(bez_asercji), sorted(DEKLARACJE_BEZ_ASERCJI)))

    # I DRUGA STRONA: kazda wymieniona ma NAPRAWDE nie byc testem. Bez tego zdanie
    # „same pomocniki\" byloby prawdziwe takze o zbiorze, ktory zawiera test.
    sprawdzonych = 0
    for _plik, nazwa in sorted(DEKLARACJE_BEZ_ASERCJI):
        assert not nazwa.startswith("test_"), (
            "`%s` jest funkcja TESTOWA bez ani jednej asercji — to nie jest trafienie "
            "falszywe, tylko usterka, i wymienia ja takze bramka asercji" % nazwa)
        sprawdzonych += 1
    assert sprawdzonych == len(DEKLARACJE_BEZ_ASERCJI), sprawdzonych

    # ASERCJI „zadna funkcja TESTOWA nie stoi tu bez asercji" TU NIE MA, i jest to
    # decyzja z pomiaru, a nie przeoczenie. Kontrola negatywna KN-2b (test z deklaracja
    # w docstringu i pustym cialem, puszczona przez CALY zestaw) dala 2475/2479: obok
    # porownania zbioru wyzej zapalily sie `test_kn2_deklaracja_bez_asercji: przeszedl
    # bez wykonania ani jednej asercji` z bramki asercji (6.D25) oraz dwie zapadki.
    # Osobne zdanie o tym samym byloby wiec CZWARTYM — a porownanie zbioru wyzej mowi
    # WIECEJ: nazywa funkcje i wiaze ja z werdyktem „100 %% trafien falszywych".


def test_sito_jest_SLEPE_na_przypadek_dla_ktorego_powstalo():
    """Trafienie pominiete: 1 na 1 — druga liczba, i ta rozstrzyga.

    Sito odpowiada „zielone" na obu czlonach pary, ktora rozni sie DOKLADNIE tym,
    czy deklarowany pomiar jest wykonywany. Para jest syntetyczna, bo drzewo niesie
    dzis tylko czlon poprawny — ale liczba pod nia jest z drzewa: w commicie
    `a5e9ff0`, ktory wprowadzil zdanie niesprawdzane niczym, funkcja miala SZESC
    asercji. Rodzina 6.D75: ten sam werdykt na wejsciu poprawnym i na wadliwym.
    """
    import ast

    wspolny_docstring = '\'\'\'Cos tam. Innych list w drzewie NIE MA, i to jest zmierzone, nie zalozone.\'\'\''
    poprawna = (
        "def test_a():\n"
        "    %s\n"
        "    assert not inne_listy_w_drzewie(), 'zdanie wyzej sprawdzone'\n" % wspolny_docstring)
    wadliwa = (
        "def test_b():\n"
        "    %s\n"
        "    assert 2 + 2 == 4, 'asercja o czym innym'\n" % wspolny_docstring)

    werdykty = []
    for zrodlo in (poprawna, wadliwa):
        fn = ast.parse(zrodlo).body[0]
        doc = ast.get_docstring(fn) or ""
        asercji = sum(1 for w in ast.walk(fn) if isinstance(w, ast.Assert))
        assert WZORZEC_DEKLARACJI_POMIARU.search(doc), (
            "wzorzec nie widzi deklaracji we wlasnym wejsciu syntetycznym — wtedy cala "
            "ta bramka mowi o niczym")
        werdykty.append(asercji == 0)

    assert werdykty == [False, False], (
        "sito rozroznilo czlony pary, ktore roznia sie TYLKO tym, czy deklarowany "
        "pomiar jest wykonywany — jesli tak, werdykt 6.D207 („odsiac sie NIE DA\") "
        "trzeba przeliczyc: %s" % werdykty)

    # KOTWICY W DRZEWIE NIE MA I BYC NIE MOZE — to jest czesc odpowiedzi, a nie brak
    # w bramce. Jedyne znane TRAFIENIE PRAWDZIWE w historii tego repozytorium zostalo
    # NAPRAWIONE przez 6.D193: docstring `test_zaden_wpis_nie_niesie_rangi_OTWARTEJ_w_tej_liscie`
    # mowi dzis „od 6.D193 jest to SPRAWDZANE, a nie przeczytane" i deklaracji pomiaru
    # juz nie niesie. Populacja trafien prawdziwych w dzisiejszym drzewie wynosi wiec
    # ZERO, a sita nie da sie sprawdzic na zbiorze pustym — stad para syntetyczna wyzej
    # i liczba historyczna nizej, wzieta z commita, ktory te usterke wprowadzil.
    assert ASERCJI_W_COMMICIE_a5e9ff0 >= 1, (
        "liczba asercji w `a5e9ff0` mowi %d — przy zerze sito ZOBACZYLOBY tamta "
        "usterke i werdykt „odsiac sie nie da\" bylby falszywy"
        % ASERCJI_W_COMMICIE_a5e9ff0)

    plik, nazwa = FUNKCJA_TRAFIENIA_POMINIETEGO
    with open(os.path.join(ROOT, plik), encoding="utf-8") as uchwyt:
        drzewo = ast.parse(uchwyt.read())
    trafiona = [w for w in ast.walk(drzewo)
                if isinstance(w, ast.FunctionDef) and w.name == nazwa]
    assert len(trafiona) == 1, (
        "`%s` nie stoi juz w `%s` — kotwica pomiaru 6.D207 wskazuje na nic"
        % (nazwa, plik))
    doc = ast.get_docstring(trafiona[0]) or ""
    assert "od 6.D193 jest to SPRAWDZANE" in doc, (
        "docstring `%s` przestal mowic, ze zdanie jest sprawdzane — jesli deklaracja "
        "wrocila bez skanu pod spodem, wraca tez usterka, od ktorej wyszlo 6.D207"
        % nazwa)



# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))


# --- 6.D218: wzorce prozy nie wymuszają formy gramatycznej po liczebniku -----------
#
# **Skąd.** Wzorzec z formą wpisaną na sztywno (`(\d+)\s+WOLNE`) żąda jednej odmiany,
# a po polsku odmiana zależy od KOŃCÓWKI liczebnika: 1 → l.poj., końcówka 2/3/4 poza
# 12–14 → l.mn. mianownik, reszta → l.mn. dopełniacz. Zapadka rośnie, więc taki wzorzec
# prędzej czy później **zapala się na zdaniu napisanym POPRAWNIE** — czyli ma kształt,
# który 6.D27 każe wyłączyć, a nie obchodzić. Obejście jest tu tanie (napisać błędnie),
# więc usterka utrwala się po cichu przy każdym podniesieniu.
#
# **Zmierzone 15.09.2026 na całej historii rejestru zapadek — błąd był ZAWSZE:**
#
#     46/17/3/25   „25 WOLNE”     (ma być WOLNYCH)
#     48/17/3/27   „27 WOLNE”     (ma być WOLNYCH)
#     49/17/3/28   „28 WOLNE”     (ma być WOLNYCH)
#     50/17/3/29   „29 WOLNE”     (ma być WOLNYCH)
#     51/17/3/30   „30 WOLNE”     (ma być WOLNYCH)
#     54/17/3/33   „54 zapadek”   (ma być zapadki — błąd PRZESKOCZYŁ o słowo)
#
# Przy 33 forma `WOLNE` zrobiła się poprawna, a błędne zrobiło się `zapadek` po 54.
# Sześć wartości, sześć błędów, za każdym razem dokładnie jeden — i ani razu nie
# zapaliło się nic, bo bramką był ten sam wzorzec, który błąd wymuszał.
#
# **ROZSTRZYGNIĘCIE: zdania zmieniają KSZTAŁT, wzorce NIE są poszerzane.** Wzorzec
# przyjmujący obie formy przestaje pilnować czegokolwiek — a kształt, w którym liczba
# stoi PO etykiecie, nie wymusza niczego i przechwytuje tyle samo. Wzór był w tym pliku
# od początku: `WZORZEC_MODULOW` czyta „dla N modulow” i jest odporny, bo przypadek
# narzuca **przyimek**, a nie liczba.

#: Przyimki, które rządzą przypadkiem SAME i zwalniają liczebnik z rządzenia nim.
#: Bez tej listy skan niżej zapaliłby się na `WZORZEC_MODULOW`, czyli na wzorcu
#: POPRAWNYM — a bramka świecąca na poprawnym tekście zostaje wyłączona, nie poprawiona.
#: Lista jest krótka i to jest jej granica, powiedziana wprost: rządzić przypadkiem
#: potrafi też czasownik i wyrażenie przyimkowe, a tych skan nie rozpoznaje.
PRZYIMKI_RZADZACE = ("dla", "do", "od", "bez", "oprocz", "oprócz", "wedlug", "według",
                     "z", "ze", "u", "spośród", "sposrod", "poza", "przy", "nad", "pod",
                     "w", "we", "na", "o", "po")

#: Wzorce prozy niosące LICZBĘ — te i tylko te mogą wymuszać formę po liczebniku.
#: `WZORZEC_DEKLARACJI_POMIARU` liczby nie niesie i do tej krotki nie należy.
WZORCE_Z_LICZBA = (
    ("WZORZEC_ZAPADEK", WZORZEC_ZAPADEK),
    ("WZORZEC_MODULOW", WZORZEC_MODULOW),
    ("WZORZEC_POMOCNIKOW", WZORZEC_POMOCNIKOW),
)

#: Przechwycenie liczby (cyframi albo słownie) i słowo, które po nim następuje.
#: **Klasa litery zapisana jako `[^\W\d_]`, a nie wyliczeniem polskich znaków** — i od
#: 16.09.2026 (6.D236) jest tak w KAŻDEJ ŻYWEJ klasie tego modułu. Akapit jest PRZEPISANY,
#: a nie dopisany obok: stało tu, że klasy wypisane z ręki „mają" uszkodzone kodowanie,
#: i było to prawdą o dwóch — `WZORZEC_POMOCNIKOW` i skan w `_liczby_slowne_w_prozie`
#: niosły w miejscu `ęŁł` jeden znak `U+A8F3` (DEVANAGARI SIGN CANDRABINDU VIRAMA).
#:
#: **Skan zatrzymywał się w środku słowa, i to w OBIE strony.** Gubił: „częściowe" czytał
#: jako „cz". Ale też ZMYŚLAŁ: „często" rozcinał na „cz" + „sto", a `sto` jest kluczem mapy
#: liczebników o wartości 100. Zmierzone 16.09.2026 na całym drzewie `.py`/`.md`:
#: **1606 zgubionych liczebników** i **31 fałszywych setek**, przy czym fałszywe biorą się
#: z WIĘCEJ niż jednego słowa — `często`, `gęsto`, a także `stoi` i `stoją`, czyli wyrazów
#: pospolitych. Z 92 kluczy mapy klasa zepsuta nie dopasowywała CAŁEGO słowa dla **24**.
#:
#: **Dlaczego klasa uniwersalna, a nie wyliczenie poprawione ręką — to jest pomiar, nie
#: gust.** Oba dają dziś na drzewie wynik IDENTYCZNY (0 zgubionych, 0 fałszywych), więc
#: liczba ich nie rozróżnia. Rozróżnia je TRYB AWARII: wyliczenie tnie słowo na każdej
#: literze, której nie wymieniono, a to drzewo nosi `é`, `è`, `à`, `µ` i `Δ` w setkach
#: wystąpień. Rozcięcie nie jest skutkiem ubocznym tej usterki, tylko jej MECHANIZMEM —
#: 31 fałszywych setek powstało dokładnie tak. Wybrana jest więc klasa, która nie tnie
#: i nie wymaga pilnowania listy.
#:
#: **Czego ta poprawka NIE naprawia i jest to zmierzone:** usterki nie łapała ANI JEDNA
#: bramka — ani przed, ani po. Przebieg z klasami zepsutymi daje `119/119`, bo ostrze
#: `MINIMUM_LICZB_SLOWNYCH` stoi setki trafień niżej niż populacja. Weryfikacją tej
#: pozycji są więc POMIARY wypisane wyżej, a nie zieleń zestawu.
#:
#: Jedyne pozostałe `U+A8F3` w tym module stoi w CYTACIE historycznym
#: (`stary_pomocnikow`) i jest tam NIECZYNNE — patrz komentarz przy nim.
_LICZBA_RZADZI = re.compile(
    r"\((?:\\d\+|\[[^\]]*\]\+)\)(?:\\s[+*]|\s)+([^\W\d_]+)", re.UNICODE)


def formy_wymuszane_po_liczebniku(wzorce=None):
    """`(nazwa, słowo)` dla każdego wzorca, w którym przechwycona LICZBA rządzi słowem.

    Czyta ŹRÓDŁO wzorca (`.pattern`), a nie prozę — bo wymuszenie jest własnością
    wzorca, nie zdania: zdanie da się napisać poprawnie tylko wtedy, gdy wzorzec na to
    pozwala. Przyimek stojący bezpośrednio przed przechwyceniem zwalnia: to on wtedy
    rządzi przypadkiem, a liczba nie ma nic do rzeczy (`WZORZEC_MODULOW`).
    """
    out = []
    for nazwa, wzorzec in (wzorce if wzorce is not None else WZORCE_Z_LICZBA):
        zrodlo = wzorzec.pattern
        for m in _LICZBA_RZADZI.finditer(zrodlo):
            # Przyimek PO liczbie — liczba nie rządzi przyimkiem, tylko tym, co za nim.
            # Bez tego warunku skan zgłaszał „1 poza zasięgiem skanu" jako wymuszenie
            # formy `poza`, czyli trafienie fałszywe na zdaniu poprawnym (6.D27).
            if m.group(1).lower() in PRZYIMKI_RZADZACE:
                continue
            przed = re.findall(r"([^\W\d_]+)[\W\d_]*$", zrodlo[:m.start()], re.UNICODE)
            if przed and przed[-1].lower() in PRZYIMKI_RZADZACE:
                continue
            out.append((nazwa, m.group(1)))
    return sorted(set(out))


def test_zaden_wzorzec_prozy_nie_wymusza_formy_po_liczebniku():
    """Zbiór PUSTY — i dlatego stoi przy nim kontrola przyrządu (6.D159).

    Pusty zbiór odpowiada „nic nie wymusza” tak samo przekonująco jak skan, który
    oślepł. Druga połowa testu podaje więc skanowi OBA kształty sprzed tej pozycji
    i żąda, żeby je zobaczył.
    """
    wymuszane = formy_wymuszane_po_liczebniku()
    assert wymuszane == [], (
        "wzorzec prozy wymusza formę gramatyczną po liczebniku: %s — po polsku forma "
        "zależy od końcówki liczby, a zapadki rosną, więc taki wzorzec zapali się "
        "kiedyś na zdaniu napisanym POPRAWNIE (6.D27). Odpowiedzią jest zmiana "
        "KSZTAŁTU zdania (liczba po etykiecie), a nie poszerzenie wzorca o obie "
        "formy — wzorzec przyjmujący obie przestaje pilnować czegokolwiek (6.D218)"
        % wymuszane)

    # KONTROLA PRZYRZĄDU: oba kształty sprzed 6.D218, podane skanowi wprost.
    stary_zapadek = re.compile(
        r"(\d+)\s+zapadek:\s*\*\*(\d+)\s+przybitych,\s*(\d+)\s+częściowe,\s*"
        r"(\d+)\s+WOLNE\s+i\s+(\d+)\s+poza\s+zasięgiem\s+skanu\.\*\*")
    # **`U+A8F3` w klasie nizej jest CYTATEM, nie usterka (6.D236).** Tak brzmial ten
    # wzorzec przed 6.D218, razem ze swoim uszkodzonym kodowaniem. Klasa jest tu
    # NIECZYNNA: `_LICZBA_RZADZI` dopasowuje ja jako `\[[^\]]*\]\+` i przechwytuje
    # dopiero slowo PO niej (`pomocniki`, czysty ASCII). Zmierzone podstawieniem
    # siedmiu roznych klas — wszystkie daja ten sam wynik. Naprawiac tu nie ma czego,
    # a poprawienie zamienilo by cytat w parafraze i skasowalo jedyny slad, ze usterka
    # jest STARSZA niz 6.D218.
    stary_pomocnikow = re.compile(
        r"([A-Za-zĄąĆćĘꣳŃńÓóŚśŹźŻż]+) pomocniki, ktore maja byc JEDYNA droga")
    widziane = formy_wymuszane_po_liczebniku(
        (("stary_zapadek", stary_zapadek), ("stary_pomocnikow", stary_pomocnikow)))
    assert widziane == [
        ("stary_pomocnikow", "pomocniki"),
        ("stary_zapadek", "WOLNE"),
        ("stary_zapadek", "częściowe"),
        ("stary_zapadek", "przybitych"),
        ("stary_zapadek", "zapadek"),
    ], (
        "skan NIE WIDZI kształtów, które ta pozycja usunęła — wtedy pusty zbiór wyżej "
        "mówi tyle, co skan, który go wypisał: %s" % widziane)

    # GRANICA, WYKONANA: przyimek zwalnia, i to jest powód, dla którego
    # `WZORZEC_MODULOW` nie jest usterką mimo kształtu „liczba, potem rzeczownik”.
    zwolniony = formy_wymuszane_po_liczebniku(
        (("z_przyimkiem", re.compile(r"robi to samo dla (\d+) modulow")),))
    assert zwolniony == [], (
        "skan zapalił się na wzorcu, w którym przypadkiem rządzi PRZYIMEK "
        "(«dla N modulow») — to jest zdanie poprawne przy każdej liczbie, "
        "a bramka ma na nim "
        "milczeć: %s" % zwolniony)


def test_forma_po_liczebniku_zgadza_sie_z_polska_odmiana():
    """Reguła odmiany, na której stoi rozstrzygnięcie wyżej — wykonana, nie opisana.

    Bez niej zdanie „błąd był przy KAŻDEJ wartości historii” byłoby prozą przy zapadce,
    czyli tym, czego ten moduł pilnuje u innych.
    """
    def forma(n):
        if n == 1:
            return "poj"
        if n % 100 in (12, 13, 14):
            return "dop"
        return "mian" if n % 10 in (2, 3, 4) else "dop"

    for liczba, oczekiwana in ((1, "poj"), (2, "mian"), (3, "mian"), (4, "mian"),
                               (5, "dop"), (12, "dop"), (13, "dop"), (14, "dop"),
                               (22, "mian"), (25, "dop"), (30, "dop"), (33, "mian"),
                               (54, "mian"), (111, "dop"), (122, "mian")):
        assert forma(liczba) == oczekiwana, (
            "odmiana po %d wyszła `%s`, a ma być `%s`" % (liczba, forma(liczba), oczekiwana))

    # Historia rejestru zapadek: przy KAŻDEJ wartości stary kształt wymuszał dokładnie
    # jedną formę błędną. Liczby z `test_tree_walks.py` i z komunikatów jego asercji.
    stary_ksztalt = {"zapadek": "dop", "przybitych": "dop", "częściowe": "mian",
                     "WOLNE": "mian"}
    historia = ((46, 17, 3, 25), (48, 17, 3, 27), (49, 17, 3, 28),
                (50, 17, 3, 29), (51, 17, 3, 30), (54, 17, 3, 33))
    for razem, przybite, czesciowe, wolne in historia:
        zle = [slowo for liczba, slowo in ((razem, "zapadek"), (przybite, "przybitych"),
                                           (czesciowe, "częściowe"), (wolne, "WOLNE"))
               if forma(liczba) != stary_ksztalt[slowo]]
        assert len(zle) == 1, (
            "przy rejestrze %d/%d/%d/%d stary kształt wymuszał %d form błędnych (%s), "
            "a pomiar 6.D218 mówi o dokładnie jednej przy każdej z sześciu wartości"
            % (razem, przybite, czesciowe, wolne, len(zle), zle))
