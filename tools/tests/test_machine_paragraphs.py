"""Akapit `docs/23-environment.md` o KONKRETNEJ maszynie ma nieść datę.

**Skąd ta bramka.** 6.D169 przeczytało ten dokument ręką i znalazło zdania mówiące
o maszynie, na której coś zmierzono — z werdyktem przy każdym, czy niesie datę.
Jedno daty nie miało i dostało ją tamtym commitem. Od tamtej pory pilnował tego
WYŁĄCZNIE ten jeden pomiar, wykonany ręką i zapisany w raporcie: następny taki
akapit, dopisany jutro, nie zapaliłby niczego.

**Dlaczego zbiór PRZYPIĘTY, a nie bramka na kształcie.** Pole „Poza zakresem"
6.D169 odrzuciło bramkę na kształcie zdania i powód zostaje: takie sito zapala się
na prozie poprawnej, czyli jest bramką z 6.D27. Zbiór przypięty nie ocenia kształtu
— zna dzisiejsze akapity i zapala się na DZIESIĄTYM, którego nikt tu nie wpisał.

**Klucz idzie po pierwszym zdaniu akapitu, nie po numerze wiersza.** 6.D169
pokazało, że numery przesuwają się przy każdej zmianie dokumentu: ten sam akapit
raport podaje raz jako 473, raz jako 474. Numer wiersza jako klucz starzeje się
więc w dobę, a pierwsze zdanie przeżywa dopisanie akapitu gdziekolwiek indziej.

**Sito jest SZERSZE niż wzorzec 6.D169 i to jest treść, nie ozdoba** (19.09.2026,
6.D285). Tamten wzorzec brzmiał `tej maszynie|tym kontenerze|czystej maszynie`
i dlatego jego tabela ma osiem wierszy. Ten sam dokument czytany razem z formą
„u mnie" daje o jeden akapit więcej — i ten dziewiąty stoi w zbiorze niżej.
Liczba z tamtego raportu jest więc własnością WZORCA, a nie dokumentu; zbiór nie
został zawężony po to, żeby się z nią zgodzić.
"""

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_message_claims as TMC  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Dokument, o którym ta bramka mówi. Rozszerzenie zbioru na inne pliki `docs/`
#: jest osobną pozycją (6.D287) i celowo nie stoi tutaj.
DOKUMENT = os.path.join(ROOT, "docs", "23-environment.md")

#: Kotwica „zdanie o maszynie". Forma „u mnie" stoi tu obok form z 6.D169, bo bez
#: niej sito nie widzi akapitu mówiącego o maszynie czytającego.
#:
#: **Forma „u siebie" była tu przez jeden przebieg i została zdjęta po obejrzeniu
#: trafienia** (19.09.2026, 6.D285). Złapała akapit o tym, że „żaden workflow nie
#: wpisuje numeru u siebie" — a tam „u siebie" znaczy „we własnym pliku", nie
#: „na własnej maszynie". Zdjęta z powodu wziętego z tekstu, a nie dlatego, że
#: psuła liczbę: gdyby trafienie było prawdziwe, akapit stanąłby w zbiorze niżej.
MASZYNA = re.compile(
    r"t(?:ej|ym)\s+(?:maszyn\w+|kontener\w+)|czyst\w+\s+(?:maszyn\w+|kontener\w+)|"
    r"\bu mnie\b", re.IGNORECASE)

#: Wzorzec daty POŻYCZONY, a nie przepisany drugi raz: własny literał z `\b` przy
#: cyfrze wpadłby do przybitego zbioru `GRANICE_PRZY_CYFRZE` bramki granic.
DATA = TMC.DATA

#: Granica zdania też pożyczona — z tego samego powodu.
GRANICA_ZDANIA = TMC.GRANICA_ZDANIA

#: Ozdobniki Markdowna zdejmowane z klucza. Bez tego zmiana pogrubienia w pierwszym
#: zdaniu zrywałaby klucz, choć akapit mówi dokładnie to samo.
OZDOBNIK = re.compile(r"[*`\"„”]")

#: Klasy akapitu. KONKRETNA mówi o maszynie, na której ktoś coś zmierzył, i ma
#: nieść datę — inaczej za rok nie wiadomo, czego dotyczy. DOWOLNA mówi o maszynie
#: czytającego albo o dowolnej czystej maszynie i daty nie potrzebuje, bo nie
#: twierdzi nic o żadnym konkretnym dniu.
KONKRETNA = "konkretna"
DOWOLNA = "dowolna"

#: **Przypięty zbiór akapitów mówiących o maszynie, z klasą i powodem przy każdym.**
#: Klucz to pierwsze zdanie akapitu, przycięte do `DLUGOSC_KLUCZA` znaków i pozbawione
#: ozdobników Markdowna. Porównywany W OBIE STRONY: nowy akapit zapala bramkę, bo go
#: tu nie ma, a zniknięcie wpisanego zapala ją, bo klucz przestał się rozwiązywać.
PRZYPIETE = {
    "Ta sekcja powstała 08.09.2026 z mojej własnej pomyłki, nie z prz":
        (KONKRETNA, "sekcja o sondzie na obecność Blendera; data stoi w pierwszym zdaniu"),
    "Czym sprawdzić — jedno polecenie na narzędzie. Zmierzone 08.09.2":
        (KONKRETNA, "pomiar na czystym środowisku zmiennych, z datą w tym samym zdaniu"),
    "Czwarte miejsce, którego żaden skrypt tego repozytorium nie twor":
        (KONKRETNA, "dwa dowiązania założone ręką, z datą i godziną"),
    "Tego nie było w opisie pozycji 6.D48 i wyszło z pomiaru.":
        (KONKRETNA, "zdanie, któremu 6.D169 dopisało datę; przed tym commitem było bez"),
    "Koszt, zmierzony 03.09.2026 na czystym kontenerze:":
        (KONKRETNA, "koszt instalacji narzędzi, data w zdaniu wprowadzającym"),
    "Zmierzone 03.09.2026 w tym kontenerze.":
        (KONKRETNA, "tabela czasów przebiegu, data w pierwszym zdaniu"),
    "Ta sekcja jest przepisana 04.09.2026, a nie dopisana obok. Poprz":
        (KONKRETNA, "przepisana sekcja o katalogu narzędzi, z datą przepisania"),
    "Rdzeń w src/Sim/ nie ma zależności NuGet, ale tests/Sim.Tests ma":
        (DOWOLNA, "mówi o PIERWSZYM uruchomieniu na czystej maszynie, czyli o dowolnej; "
                  "6.D169 wskazało ten akapit jako stojący poza populacją"),
    "BLENDER_BIN i GODOT_BIN są tymi dwiema, o które doctor.sh pyta w":
        (DOWOLNA, "rozjazd `u mnie ok, w CI czerwono` opisuje maszynę czytającego, "
                  "a nie żadną konkretną; wzorzec 6.D169 tego akapitu nie widział"),
}

#: Ile znaków pierwszego zdania wchodzi do klucza. Krótszy klucz zlewałby akapity
#: zaczynające się tak samo, dłuższy zrywałby się przy poprawce w środku zdania.
DLUGOSC_KLUCZA = 64

#: Podłoga na liczbę akapitów przeczytanych w dokumencie. Bez niej czytnik zepsuty
#: do zera przechodziłby zbiór przypięty CELUJĄCO, bo pusty zbiór akapitów zgadza
#: się z każdym oczekiwaniem o nieobecności (6.D27).
MINIMUM_AKAPITOW = 140


def akapity(sciezka):
    """`[(pierwszy_wiersz, tekst, ile_wierszy)]` — akapit sklejony w JEDEN napis.

    Sklejenie jest tu treścią, a nie wygodą: `grep` dopasowuje w obrębie wiersza,
    więc sformułowanie rozcięte przez zawijanie jest dla niego niewidoczne. 6.D169
    zmierzyło to na tym samym dokumencie — jego pole „Weryfikacja" podawało liczbę
    o jeden mniejszą od liczby akapitów właśnie z tego powodu.
    """
    with io.open(sciezka, encoding="utf-8") as uchwyt:
        linie = uchwyt.read().split("\n")
    out, bufor, od = [], [], None
    for numer, linia in enumerate(linie, 1):
        if linia.strip():
            if od is None:
                od = numer
            bufor.append(linia)
        elif bufor:
            out.append((od, " ".join(b.strip() for b in bufor), len(bufor)))
            bufor, od = [], None
    if bufor:
        out.append((od, " ".join(b.strip() for b in bufor), len(bufor)))
    return out


def klucz(tekst):
    """Pierwsze zdanie akapitu, bez ozdobników, przycięte — klucz zbioru."""
    pierwsze = GRANICA_ZDANIA.split(tekst)[0]
    return re.sub(r"\s+", " ", OZDOBNIK.sub("", pierwsze)).strip()[:DLUGOSC_KLUCZA]


def akapity_o_maszynie(sciezka=None):
    """`[(klucz, pierwszy_wiersz, tekst)]` dla akapitów, które sito uznaje za mówiące
    o maszynie. Argument `sciezka` dochodzi TU, a nie do stałej modułowej: bez tego
    kontrola na pliku próbnym mierzyłaby dokument drzewa roboczego (6.D281)."""
    return [(klucz(tekst), od, tekst)
            for od, tekst, _ in akapity(sciezka or DOKUMENT)
            if MASZYNA.search(tekst)]


def nieprzypiete(sciezka=None):
    """Akapity o maszynie, których w zbiorze przypiętym nie ma — po kluczu."""
    return [(k, od) for k, od, _ in akapity_o_maszynie(sciezka) if k not in PRZYPIETE]


def konkretne_bez_daty(sciezka=None):
    """Akapity klasy KONKRETNA, w których nie stoi ani jedna data.

    Akapity spoza zbioru liczą się tu jako KONKRETNE i to jest wybór: nowy akapit
    o maszynie domyślnie musi nieść datę, a zaklasyfikowanie go jako DOWOLNY jest
    decyzją, którą ktoś podejmuje wpisem do zbioru, a nie milczeniem.
    """
    out = []
    for k, od, tekst in akapity_o_maszynie(sciezka):
        klasa = PRZYPIETE.get(k, (KONKRETNA, ""))[0]
        if klasa == KONKRETNA and not DATA.search(tekst):
            out.append((k, od))
    return out


def test_czytnik_widzi_caly_dokument_a_nie_jego_resztke():
    """**Podłoga na populację — bez niej zbiór przypięty zgadza się z pustką.**

    Czytnik zepsuty do zera nie znajduje żadnego akapitu o maszynie, więc zbiór
    przypięty „nie ma nadmiarowych" przechodzi celująco. Ta podłoga odróżnia
    „dokument nie urósł" od „czytnik oślepł".
    """
    ile = len(akapity(DOKUMENT))
    assert ile >= MINIMUM_AKAPITOW, (
        "akapitow w dokumencie jest %d przy podlodze %d — czytnik oslepl albo "
        "dokument zostal skrocony o polowe" % (ile, MINIMUM_AKAPITOW))


def test_zbior_przypiety_zgadza_sie_z_dokumentem_W_OBIE_STRONY():
    """**Dziesiąty akapit o maszynie zapala bramkę, a zniknięcie wpisanego też.**

    To jest cała treść pozycji 6.D285: dotąd nowy akapit o maszynie nie zapalał
    niczego, bo pilnował go wyłącznie jeden pomiar wykonany ręką.
    """
    widziane = {k for k, _, _ in akapity_o_maszynie()}
    doszly = sorted(widziane - set(PRZYPIETE))
    zniknely = sorted(set(PRZYPIETE) - widziane)
    assert doszly == [], (
        "akapit o maszynie, ktorego w zbiorze przypietym nie ma: %s — dopisz go "
        "z klasa i powodem albo zdejmij zdanie o maszynie z dokumentu" % doszly)
    assert zniknely == [], (
        "wpis zbioru, ktoremu nie odpowiada zaden akapit: %s — pierwsze zdanie "
        "akapitu zostalo zmienione albo akapit zniknal, wiec popraw wpis" % zniknely)


def test_kazdy_akapit_o_KONKRETNEJ_maszynie_niesie_date():
    """**Twierdzenie, dla którego 6.D169 powstało — odtąd pilnowane, a nie zapisane.**

    Akapit o maszynie, na której coś zmierzono, bez daty starzeje się po cichu:
    za pół roku nie wiadomo, czy mówi o dzisiejszym kontenerze, czy o tamtym.
    """
    gole = konkretne_bez_daty()
    assert gole == [], (
        "akapit o KONKRETNEJ maszynie bez daty: %s — dopisz date zmierzona "
        "z historii (`git log -S`), a nie zgadnieta" % gole)


def _plik_probny(katalog, wiersze):
    sciezka = os.path.join(katalog, "probny.md")
    with io.open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write("\n".join(wiersze) + "\n")
    return sciezka


def test_akapit_SPOZA_zbioru_zapala_i_komunikat_go_NAZYWA():
    """**Kontrola negatywna: bramka ma NAZWAĆ akapit, a nie podać samą liczbę.**

    6.D169 zmierzyło, że licznik „bez daty" nie odróżnia akapitu dopisanego od
    skasowanego. Dlatego sprawdzane jest tu, że akapit trafia na listę pod swoim
    kluczem — komunikat z samą liczbą spełniałby asercję i nic by nie mówił.
    """
    import tempfile
    with tempfile.TemporaryDirectory(prefix="metro-maszyna-") as katalog:
        sciezka = _plik_probny(katalog, [
            "Wstep bez maszyny.",
            "",
            "Na tej maszynie dziala wszystko, co ma dzialac.",
            "",
            "Drugi akapit, tez bez maszyny.",
        ])
        nowe = nieprzypiete(sciezka)
        gole = konkretne_bez_daty(sciezka)
    klucze = [k for k, _ in nowe]
    assert klucze == ["Na tej maszynie dziala wszystko, co ma dzialac."], (
        "akapit o maszynie spoza zbioru dal %r — bramka ma go wypisac pod jego "
        "wlasnym kluczem" % (klucze,))
    assert [k for k, _ in gole] == klucze, (
        "akapit spoza zbioru nie trafil na liste `bez daty` — akapit nieznany ma "
        "byc domyslnie KONKRETNY, inaczej nowy akapit przechodzi milczeniem")


def test_akapit_o_maszynie_DOWOLNEJ_i_akapit_z_DATA_nie_zapalaja_daty():
    """**Kontrola przyrządu, dwustronna — bramka ma odsiewać, a nie zapalać się zawsze.**

    Sito, które zapala się także na akapicie z datą, daje listę pustą z powodu,
    o którym nic nie mówi.
    """
    import tempfile
    with tempfile.TemporaryDirectory(prefix="metro-maszyna-") as katalog:
        sciezka = _plik_probny(katalog, [
            "Na tej maszynie, w kontenerze z 08.09.2026, dziala wszystko.",
            "",
            "Pierwsze uruchomienie na czystej maszynie potrzebuje sieci.",
        ])
        gole = [k for k, _ in konkretne_bez_daty(sciezka)]
        widziane = [k for k, _, _ in akapity_o_maszynie(sciezka)]
    assert len(widziane) == 2, (
        "sito widzi %d akapitow, a oba mowia o maszynie — kontrola przyrzadu "
        "przestala byc kontrola" % len(widziane))
    assert gole == ["Pierwsze uruchomienie na czystej maszynie potrzebuje sieci."], (
        "na liscie `bez daty` stoi %r — akapit Z DATA ma z niej wypasc, a akapit "
        "o maszynie dowolnej ma na niej stanac, dopoki nikt nie wpisze go do "
        "zbioru z klasa DOWOLNA" % (gole,))


def test_klucz_PRZEZYWA_przesuniecie_numerow_wierszy():
    """**Powód, dla którego kluczem jest zdanie, a nie numer wiersza.**

    Dopisanie akapitu na początku dokumentu przesuwa numery wszystkich następnych.
    Klucz po numerze zerwałby się wtedy na każdym wpisie naraz, choć żadnego
    z tych akapitów nikt nie tknął.
    """
    import tempfile
    tresc = ["Na tej maszynie, w kontenerze z 08.09.2026, dziala wszystko."]
    with tempfile.TemporaryDirectory(prefix="metro-maszyna-") as katalog:
        przed = akapity_o_maszynie(_plik_probny(katalog, tresc))
        po = akapity_o_maszynie(_plik_probny(
            katalog, ["Akapit dopisany wyzej.", ""] + tresc))
    assert [k for k, _, _ in przed] == [k for k, _, _ in po], (
        "klucz zmienil sie po dopisaniu akapitu wyzej — czytnik kotwiczy po "
        "numerze wiersza, a mial po pierwszym zdaniu")
    assert [od for _, od, _ in przed] != [od for _, od, _ in po], (
        "numery wierszy sie NIE przesunely, wiec kontrola nie sprawdzila tego, "
        "co mysli, ze sprawdza")


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
