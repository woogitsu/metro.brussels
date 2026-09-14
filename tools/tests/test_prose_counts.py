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
WZORZEC_ZAPADEK = re.compile(
    r"(\d+)\s+zapadek:\s*\*\*(\d+)\s+przybitych,\s*(\d+)\s+częściowe,\s*"
    r"(\d+)\s+WOLNE\s+i\s+(\d+)\s+poza\s+zasięgiem\s+skanu\.\*\*")

#: Zdanie o liczbie modułów zestawu.
WZORZEC_MODULOW = re.compile(r"robi to samo dla (\d+) modulow")

#: Zdanie o liczbie pomocników parsujących liczby (`test_runner_number_parsing.py`).
#: **Zapisane SŁOWNIE — i to jest cały powód, dla którego ta deklaracja tu doszła**
#: (6.D203). Znalazł ją skan liczebników opisany niżej; do 14.09.2026 nie porównywało
#: jej z niczym ani jedno wywołanie, a `len(POMOCNIKI)` nie było przybite w drzewie
#: nigdzie. Czwarty pomocnik dopisany do krotki zostawiłby to zdanie nieprawdziwym
#: i nikt by się o tym nie dowiedział — dokładnie ten kształt, który ten moduł łapie.
WZORZEC_POMOCNIKOW = re.compile(
    r"([A-Za-zĄąĆćĘꣳŃńÓóŚśŹźŻż]+) pomocniki, ktore maja byc JEDYNA droga")

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
    slownie = ("#: Trzydzieści osiem zapadek: **13 przybitych, 3 częściowe,\n"
               "#: 21 WOLNYCH i 1 poza zasięgiem skanu.**")
    assert WZORZEC_ZAPADEK.findall(slownie) == [], (
        "czytnik zobaczył deklarację zapisaną słownie — wtedy zapis słowny "
        "przestaje być głośnym brakiem, a staje się cichym obejściem")

    cyframi = ("#: 42 zapadek: **15 przybitych, 3 częściowe, 23 WOLNE "
               "i 1 poza zasięgiem skanu.**")
    assert WZORZEC_ZAPADEK.findall(cyframi) == [("42", "15", "3", "23", "1")], (
        "czytnik przestał widzieć deklarację zapisaną cyframi — kontrola wyżej "
        "mierzyłaby wtedy nie obejście, tylko własną ślepotę: %s"
        % WZORZEC_ZAPADEK.findall(cyframi))


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

    # WIELKOŚĆ LITERY ZDEJMOWANA TUTAJ, a nie dopisywana do mapy drugim kluczem:
    # deklaracja zaczyna zdanie, więc stoi z wielkiej („Trzy pomocniki"), a mapa ma
    # służyć też skanowi, który czyta środek zdania. Dwa klucze na to samo słowo
    # rozjechałyby się przy pierwszej edycji jednego z nich.
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
    ("test_runner_number_parsing.py", "Trzy pomocniki, ktore maja byc JEDYNA droga"),
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
                    r"[A-Za-zĄąĆćĘꣳŃńÓóŚśŹźŻż]+", wiersz)
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


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
