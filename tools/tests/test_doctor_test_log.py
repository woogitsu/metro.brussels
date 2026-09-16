#!/usr/bin/env python3
"""`doctor.sh` przy padniętym zestawie WYPISUJE dowód, a nie ścieżkę do niego.

**Skąd ta bramka (6.D241, 16.09.2026).** Do tego dnia blok „Testy narzędzi" w
`doctor.sh` kończył się przy porażce jednym wierszem:

    BLAD  testy nie przechodzą — zobacz /tmp/mbxl_tests.log

Zdanie prawdziwe wyłącznie na maszynie, na której się stało. W CI ten plik leży
poza workspace i **nie jest zbierany do artefaktów**. Zmierzone tego dnia na dwóch
przebiegach `blender-smoke` (joby **104696967107** i **104702701634**, maszyna
`docker-runner-04`, **dwie różne gałęzie**): jedyny ślad po padniętym zestawie w
całym logu joba to ten jeden wiersz, a artefakt melduje „1 file uploaded" i **1393**
oraz **1394 bajty** — czyli sam `build/t010/report.txt`. Nazwy padającego testu nie
dało się odzyskać z niczego, co CI zachowało.

To ta sama rodzina co 6.D27: **przyrząd melduje wynik, którego nie pokazuje**.
Różnica wobec 6.D27 jest taka, że tu nie chodzi o bramkę zapalającą się na poprawnym
kodzie, tylko o porażkę, której NIE DA SIĘ zdiagnozować — a `CLAUDE.md` §5 zakazuje
form weryfikacji typu „skrypt wykonał się bez błędu" właśnie dlatego, że komunikat
bez wyjścia nie jest wynikiem.

**Dlaczego wyciąg, a nie `tail`, i to jest liczba, nie wrażenie.** Zielony przebieg
zestawu z tego samego dnia ma **2836 wierszy**, a wiersz `N/M przeszło` stoi na
**2707** — czyli **129 od końca**; za nim idzie wyłącznie lista czasów 126 modułów.
`tail -n 100` nie sięga więc nawet do podsumowania, a wiersze `FAIL` zestaw wypisuje
w trakcie pętli po modułach, czyli są rozrzucone po całej długości logu.

**Czego ta bramka NIE robi:** nie rusza treści zestawu, progów czasowych ani
workflowów. Pyta wyłącznie o to, czy doctor pokazuje to, o czym mówi.
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCTOR = os.path.join(ROOT, "doctor.sh")

#: Marker wpisany do atrapy zestawu. Nie jest to napis z prawdziwego przebiegu —
#: ma być rozpoznawalny właśnie dlatego, że nigdzie indziej nie występuje.
MARKER = "test_atrapa_ktora_ma_sie_pokazac"

#: Ile wierszy `FAIL` atrapa wypisuje. Więcej niż sufit `WYCIAG_FAILI`, żeby dało się
#: zmierzyć, że sufit DZIAŁA, a nie tylko że stoi w pliku.
ILE_FAILI = 45

#: Sufit z `doctor.sh`. Czytany z pliku, nie wpisany drugi raz — zapadka na rozjazd
#: między tą bramką a kodem, którego pilnuje (6.D213: pożycz czytnik, nie pisz kopii).
def sufit_wyciagu():
    with open(DOCTOR, encoding="utf-8") as uchwyt:
        tresc = uchwyt.read()
    dopasowanie = re.search(r"^WYCIAG_FAILI=\$\{MBXL_WYCIAG_FAILI:-(\d+)\}$",
                            tresc, re.MULTILINE)
    assert dopasowanie, "w doctor.sh nie ma przypisania WYCIAG_FAILI z wartością domyślną"
    return int(dopasowanie.group(1))


ATRAPA_CZERWONA = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("  [BAJTKOD] wyczyszczono 0 kat.")
for i in range(%d):
    print("  FAIL %s_%%03d: AssertionError: atrapa" %% i)
print()
print("  2/2500 przeszło")
print("  RAZEM 1.000 s, 2500 testów, 126 modułów")
sys.exit(1)
''' % (ILE_FAILI, MARKER)

ATRAPA_ZIELONA = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
print("  2500/2500 przeszło")
print("  RAZEM 1.000 s, 2500 testów, 126 modułów")
'''

ATRAPA_BEZ_FAILI = '''#!/usr/bin/env python3
import sys
print("ModuleNotFoundError: No module named 'yaml'")
sys.exit(1)
'''


#: Ile wierszy ma atrapa DŁUGA. Prawdziwy log zestawu ma **2836** wierszy (zmierzone
#: 16.09.2026), a atrapa czerwona wyżej — **49**. Różnica nie jest kosmetyczna: bramka
#: oglądająca wyłącznie krótki log jest ślepa na KAŻDE zachowanie zależne od rozmiaru.
#: Zmierzone: mutacja `doctor.sh` odsyłająca do pliku przy logu dłuższym niż 200 wierszy
#: przechodziła **5/5**, przywracając w CI dokładnie stan sprzed 6.D241.
WIERSZY_DLUGIEJ_ATRAPY = 2900

#: Na którym wierszu długiej atrapy stoi PIERWSZY `FAIL`. Blisko początku, bo zestaw
#: wypisuje `FAIL` w trakcie pętli po modułach — i dlatego `tail` jest złym przyrządem.
WIERSZ_PIERWSZEGO_FAILA = 12

ATRAPA_DLUGA = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
for i in range(%d):
    if i == %d:
        print("  FAIL %s_poczatek: AssertionError: atrapa")
    elif i == %d - 40:
        print("  FAIL %s_koniec: AssertionError: atrapa")
    else:
        print("  ok   test_wypelniacz_%%05d" %% i)
print()
print("  2/2500 przesz\u0142o")
print("  RAZEM 1.000 s, 2500 test\u00f3w, 126 modu\u0142\u00f3w")
sys.exit(1)
''' % (WIERSZY_DLUGIEJ_ATRAPY, WIERSZ_PIERWSZEGO_FAILA, MARKER,
        WIERSZY_DLUGIEJ_ATRAPY, MARKER)

#: Trzy postaci `FAIL`, które zestaw wypisuje POZA pętlą po testach — `test_all.py`
#: wiersze 743, 748 i 753. To one opisują padnięcia typu 6.D240 (przerwany przebieg,
#: mniej wykonanych niż odkrytych, bramka asercji), a żadna nie ma po `FAIL` nazwy
#: zaczynającej się od `test_`. Bramka, która zna wyłącznie `FAIL test_...`, jest na nie
#: ślepa — zmierzone: zawężenie grepa w `doctor.sh` do `FAIL test_` przechodziło **5/5**.
POSTACIE_FAILA_ZESTAWU = ("<przebieg>", "<zestaw>", "<bramka asercji>")

ATRAPA_Z_BAJTEM_NUL = (
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "linia = b'  FAIL %s_nul: AssertionError: ' + bytes([0]) + b' atrapa'\n"
    "sys.stdout.buffer.write(linia + bytes([10]))\n"
    "sys.stdout.buffer.write('  1/2500 przesz\\u0142o'.encode() + bytes([10]))\n"
    "sys.stdout.buffer.flush()\n"
    "sys.exit(1)\n"
) % MARKER

ATRAPA_FAILE_ZESTAWU = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("  FAIL <przebieg>: przerwany przez KeyboardInterrupt")
print("  FAIL <zestaw>: wykonano 12 z 2500 odkrytych test\u00f3w, r\u00f3\u017cnica 2488")
print("  FAIL <bramka asercji>: test_atrapa")
print()
print("  0/2500 przesz\u0142o")
sys.exit(1)
'''


def _drzewo_z_atrapa(tmp, zrodlo_atrapy):
    """Drzewo symlinków do repozytorium z podmienionym `tools/tests/test_all.py`.

    Ta sama technika, co w `test_doctor_queue_claim._doctor_w_kopii`: doctor sprawdza
    kilkanaście ścieżek i przy braku którejkolwiek nie dochodzi do bloku testów, więc
    kopia częściowa nie odpowiedziałaby na pytanie tego testu. Podmieniony jest
    dokładnie jeden plik, na trzech piętrach symlinków.
    """
    drzewo = os.path.join(tmp, "repo")
    os.makedirs(drzewo)
    for nazwa in os.listdir(ROOT):
        if nazwa != "tools":
            os.symlink(os.path.join(ROOT, nazwa), os.path.join(drzewo, nazwa))
    tools = os.path.join(drzewo, "tools")
    os.makedirs(tools)
    for nazwa in os.listdir(os.path.join(ROOT, "tools")):
        if nazwa != "tests":
            os.symlink(os.path.join(ROOT, "tools", nazwa), os.path.join(tools, nazwa))
    testy = os.path.join(tools, "tests")
    os.makedirs(testy)
    for nazwa in os.listdir(os.path.join(ROOT, "tools", "tests")):
        if nazwa != "test_all.py":
            os.symlink(os.path.join(ROOT, "tools", "tests", nazwa),
                       os.path.join(testy, nazwa))
    sciezka = os.path.join(testy, "test_all.py")
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(zrodlo_atrapy)
    os.chmod(sciezka, 0o755)
    return drzewo


def _doctor_z_atrapa(zrodlo_atrapy):
    """PRAWDZIWY `doctor.sh`, atrapa zestawu, atrapa `dotnet`, bez `--no-tests`.

    **`--no-tests` jest tu wykluczone z definicji**: pytanie brzmi, co doctor robi
    w bloku testów, a ta flaga ten blok pomija. Atrapa zestawu kończy się w ułamku
    sekundy, więc koszt jest ten sam, co przy `--no-tests` — ale mierzona jest
    gałąź, o którą chodzi.

    **`MBXL_DOCTOR_RUNNING` musi zostać ZDJĘTE, i to nie jest ostrożność na zapas.**
    `doctor.sh` eksportuje tę zmienną, a `CLAUDE.md` §5 i `tools/ci/blender_smoke.sh`
    każą uruchamiać zestaw WŁAŚNIE przez doctora — czyli w CI ten moduł biegnie
    z ustawionym markerem. Bez zdjęcia go zagnieżdżony doctor wypisałby „Testy:
    pomijam" i bramka sprawdzałaby gałąź, której nie dotyczy: zielona w jobie
    `tools`, zielona w `blender-smoke`, i ślepa w obu.
    """
    with tempfile.TemporaryDirectory() as tmp:
        drzewo = _drzewo_z_atrapa(tmp, zrodlo_atrapy)

        dotnet = os.path.join(tmp, "bin", "dotnet")
        os.makedirs(os.path.dirname(dotnet), exist_ok=True)
        pin = _pin_sdk()
        with open(dotnet, "w", encoding="utf-8") as uchwyt:
            uchwyt.write("#!/bin/sh\n"
                         'if [ "$1" = "--version" ]; then echo "%s"; exit 0; fi\n'
                         'if [ "$1" = "--list-sdks" ]; then echo "%s [/atrapa]"; exit 0; fi\n'
                         "exit 1\n" % (pin, pin))
        os.chmod(dotnet, 0o755)

        srodowisko = dict(os.environ)
        srodowisko.pop("MBXL_DOCTOR_RUNNING", None)
        # `MBXL_WYCIAG_FAILI` zdejmowane z TEGO SAMEGO powodu, o jeden krok dalej.
        # Bez tego bramka zapala się na kodzie CAłKOWICIE POPRAWNYM: wystarczy, że ktoś
        # uruchomi zestaw z ustawioną zmienną, którą `doctor.sh` sam przewiduje,
        # i `test_wyciag_ma_SUFIT...` melduje rozjazd sufitu (zmierzone: `MBXL_WYCIAG_FAILI=10`
        # daje **4/5**, kod nietknięty). To jest 6.D27 w czystej postaci — bramka musi być
        # hermetyczna wobec tej jednej zmiennej, o którą pyta.
        srodowisko.pop("MBXL_WYCIAG_FAILI", None)
        srodowisko.update(DOTNET_BIN=dotnet, LC_ALL="C.UTF-8",
                          TMPDIR=os.path.join(tmp, "log"))
        os.makedirs(srodowisko["TMPDIR"], exist_ok=True)
        wynik = subprocess.run(["bash", DOCTOR], cwd=drzewo, env=srodowisko,
                               capture_output=True, text=True, timeout=180)
        return wynik.stdout + wynik.stderr


def _pin_sdk():
    with open(os.path.join(ROOT, "global.json"), encoding="utf-8") as uchwyt:
        tresc = uchwyt.read()
    dopasowanie = re.search(r'"version"\s*:\s*"([0-9.]+)"', tresc)
    assert dopasowanie, "global.json bez pinu wersji SDK"
    return dopasowanie.group(1)


def test_padniety_zestaw_POKAZUJE_nazwy_padlych_testow_a_nie_sciezke_do_pliku():
    """Wypis zawiera nazwy z wierszy `FAIL`, nie samo odesłanie do logu.

    To jest asercja, która w wersji sprzed 6.D241 nie przechodzi: tamten doctor
    wypisywał wyłącznie ścieżkę.
    """
    wypis = _doctor_z_atrapa(ATRAPA_CZERWONA)
    assert "BLAD" in wypis, wypis[-2000:]
    assert MARKER + "_000" in wypis, (
        "doctor nie pokazał ani jednej nazwy padłego testu; wypis:\n" + wypis[-2000:])
    assert "2/2500 przesz" in wypis, (
        "doctor nie pokazał podsumowania zestawu; wypis:\n" + wypis[-2000:])


def test_wyciag_ma_SUFIT_i_sufit_jest_czytany_z_doctora_a_nie_wpisany_drugi_raz():
    """Atrapa daje 45 wierszy `FAIL`, doctor pokazuje dokładnie tyle, ile deklaruje.

    Bez tej asercji sufit byłby liczbą stojącą w pliku i nierobiącą nic — a wypis
    przy padniętym module potrafi mieć kilkadziesiąt wierszy i ma zmieścić się w logu
    joba oraz w `build/t010/report.txt`.
    """
    sufit = sufit_wyciagu()
    assert sufit < ILE_FAILI, (
        "atrapa musi dawać WIĘCEJ wierszy niż sufit, inaczej sufitu nie widać: "
        "sufit=%d, atrapa=%d" % (sufit, ILE_FAILI))
    wypis = _doctor_z_atrapa(ATRAPA_CZERWONA)
    pokazane = re.findall(MARKER + r"_\d{3}", wypis)
    assert len(pokazane) == sufit, (
        "doctor pokazał %d wierszy FAIL, a sufit WYCIAG_FAILI wynosi %d"
        % (len(pokazane), sufit))
    assert "%d" % ILE_FAILI in wypis, (
        "wypis nie mówi, ILE wierszy FAIL było naprawdę — sufit bez tej liczby "
        "milczy o tym, że coś uciął")


def test_zielony_zestaw_NIE_wysypuje_logu_do_wypisu():
    """Kontrola przyrządu z drugiej strony: przy sukcesie doctor zostaje krótki.

    Bramka, która żąda wypisu ZAWSZE, zamieniłaby doctora w narzędzie wypisujące
    log przy każdym uruchomieniu — a `CLAUDE.md` §2 każe wołać go przed każdym
    zadaniem. Ta asercja mierzy, że gałąź sukcesu została nietknięta.
    """
    wypis = _doctor_z_atrapa(ATRAPA_ZIELONA)
    assert "2500/2500 przesz" in wypis, wypis[-2000:]
    assert "wiersze FAIL" not in wypis, (
        "doctor wypisał wyciąg przy ZIELONYM zestawie; wypis:\n" + wypis[-2000:])


def test_padniecie_POZA_cialem_testu_jest_nazwane_a_nie_przemilczane():
    """Zestaw, który padł bez ani jednego `FAIL`, dostaje własne zdanie.

    To nie jest przypadek hipotetyczny i dlatego ma osobną gałąź: 15.09.2026 cztery
    joby padły na `ModuleNotFoundError: No module named 'yaml'` (6.D240), czyli przed
    wykonaniem jakiegokolwiek ciała testu. Wyciąg szukający wyłącznie wierszy `FAIL`
    byłby wtedy PUSTY — a pusty wypis czyta się jak brak problemu.
    """
    wypis = _doctor_z_atrapa(ATRAPA_BEZ_FAILI)
    assert "ANI JEDNEGO wiersza FAIL" in wypis, (
        "doctor przemilczał padnięcie bez wierszy FAIL; wypis:\n" + wypis[-2000:])
    assert "No module named 'yaml'" in wypis, (
        "doctor nie pokazał ogona logu przy padnięciu poza ciałem testu; wypis:\n"
        + wypis[-2000:])


def test_doctor_NIE_odsyla_juz_do_pliku_zamiast_pokazac_jego_tresc():
    """Zdanie „zobacz <ścieżka>" zniknęło z gałęzi porażki — czytane z pliku.

    Asercja na TREŚĆ `doctor.sh`, nie na przebieg, i stoi obok przebiegowych celowo:
    wypis mógłby powstać jako DRUGI komunikat obok starego, a wtedy trzy asercje
    wyżej byłyby zielone, mimo że mylące zdanie zostało. Ta pyta o to, że blok został
    przepisany, a nie dopisany obok.
    """
    with open(DOCTOR, encoding="utf-8") as uchwyt:
        tresc = uchwyt.read()
    galaz = tresc[tresc.index('echo "Testy narz'):]
    galaz = galaz[:galaz.index("Testy rdzenia symulacji")]
    assert "wypisz_wyciag_z_logu" in galaz, galaz
    assert "nie przechodzą — zobacz" not in galaz, (
        "gałąź porażki nadal odsyła do pliku zamiast pokazać jego treść:\n" + galaz)


def test_wyciag_dziala_takze_na_logu_WIELKOSCI_PRAWDZIWEJ_a_nie_tylko_na_krotkiej_atrapie():
    """Log **2900 wierszy** — bramka ogląda rozmiar, który naprawdę występuje.

    **Skąd ta asercja (16.09.2026, adwersaryjny przegląd 6.D241).** Atrapa czerwona ma
    **49** wierszy, a prawdziwy log zestawu — **2836**. Cała pozycja 6.D241 wyszła
    z liczby o rozmiarze logu (`N/M przeszło` stoi **129 od końca**), a bramka
    oglądała wyłącznie log krótki — czyli była ślepa na każde zachowanie zależne od
    rozmiaru. **Zmierzone:** mutacja `doctor.sh` odsyłająca do pliku przy logu dłuższym
    niż 200 wierszy przechodziła **5/5**, a w CI czytający dostawał samą ścieżkę —
    dokładnie stan sprzed tej pozycji. Asercja `"nie przechodzą — zobacz" not in galaz`
    tego nie łapie, bo mutacja pisze napis własny.

    Pytanie jest o `FAIL` z **początku** logu, nie z końca: to on odróżnia wyciąg
    od `tail`, i to on znika pierwszy przy każdej mutacji składającej wypis z ogona.
    """
    wypis = _doctor_z_atrapa(ATRAPA_DLUGA)
    assert MARKER + "_poczatek" in wypis, (
        "doctor nie pokazał `FAIL` z POCZĄTKU logu długiego na %d wierszy — wyciąg "
        "został złożony z ogona albo w ogóle się nie odbył; wypis:\n%s"
        % (WIERSZY_DLUGIEJ_ATRAPY, wypis[-2000:]))
    assert MARKER + "_koniec" in wypis, (
        "doctor pokazał `FAIL` z początku, a zgubił ten z końca — wyciąg czyta CAŁY log, "
        "a nie jego kawałek; wypis:\n" + wypis[-2000:])
    assert "2/2500 przesz" in wypis, (
        "doctor nie pokazał podsumowania przy długim logu; wypis:\n" + wypis[-2000:])


def test_wyciag_zna_TRZY_postaci_FAILA_zestawu_a_nie_tylko_FAIL_test():
    """`FAIL <przebieg>`, `FAIL <zestaw>`, `FAIL <bramka asercji>` — 6.D240 wyglądało tak.

    **Skąd ta asercja.** `test_all.py` wypisuje w wierszach 743, 748 i 753 trzy postaci
    `FAIL`, w których po słowie `FAIL` **nie stoi nazwa testu**. Bramka znająca wyłącznie
    `FAIL test_...` jest na nie ślepa, a to właśnie one opisują padnięcia całego przebiegu —
    ten sam kształt, który miało 6.D240. **Zmierzone:** zawężenie grepa w `doctor.sh`
    do `^[[:space:]]*FAIL test_` przechodziło **5/5**, mimo że gubi wszystkie trzy.
    """
    wypis = _doctor_z_atrapa(ATRAPA_FAILE_ZESTAWU)
    # NAJPIERW gałąź, potem treść — i ta kolejność jest tu wynikiem pomiaru, nie stylem.
    # Pierwsza wersja tej bramki pytała wyłącznie „czy te trzy napisy są w wypisie" i
    # przechodziła **8/8** przy grepie zawężonym do `FAIL test_`: zawężenie wypycha przebieg
    # do gałęzi „zero wierszy FAIL", a ta pokazuje OGON logu — w którym te same trzy napisy
    # stoją. Bramka mierzyła więc ogon, nie wyciąg. Asercja na gałąź zamyka tę drogę.
    assert "wiersze FAIL (" in wypis, (
        "doctor poszedł gałęzią „zero wierszy FAIL” — czyli grep nie widzi `FAIL` bez "
        "nazwy testu, a to właśnie tak wygląda padnięcie całego przebiegu; wypis:\n"
        + wypis[-2000:])
    brakujace = [postac for postac in POSTACIE_FAILA_ZESTAWU if postac not in wypis]
    assert not brakujace, (
        "doctor zgubił %s — wyciąg widzi wyłącznie `FAIL` z nazwą testu, a padnięcie "
        "całego przebiegu nazwy testu nie ma; wypis:\n%s"
        % (brakujace, wypis[-2000:]))
    assert "0/2500 przesz" in wypis, wypis[-2000:]


def test_jeden_bajt_NUL_w_logu_NIE_zamienia_doctora_w_zmyslacza_przyczyny():
    """Log z bajtem spoza tekstu dalej daje nazwę, a nie zdanie o „padnięciu poza testem".

    **Skąd ta asercja (16.09.2026, adwersaryjny przegląd 6.D241).** GNU grep bez `-a`
    uznaje plik z bajtem NUL za binarny: wypisuje `binary file matches` na **stderr**
    (które `2>/dev/null` zjada) i oddaje **puste stdout**. Pusty wynik wpadał w gałąź
    „zestaw padł POZA ciałem testu", czyli doctor **twierdził przyczynę, której nie
    zmierzył** — a wiersz `FAIL` i wiersz `N/M przeszło` w logu STAŁY. To jest gorsze
    niż stan sprzed 6.D241: stary komunikat nie mówił nic, nowy mówiłby nieprawdę,
    czyli byłby dokładnie tym, co ten projekt tropi od 6.D27.

    Bajt spoza tekstu nie jest tu hipotezą: `tools/ci/blender_smoke.sh` przechwytuje
    stdout **i** stderr uruchamianych procesów do jednego pliku.
    """
    wypis = _doctor_z_atrapa(ATRAPA_Z_BAJTEM_NUL)
    assert MARKER + "_nul" in wypis, (
        "doctor zgubił wiersz `FAIL` z powodu jednego bajtu NUL; wypis:\n"
        + wypis[-2000:])
    assert "ANI JEDNEGO wiersza FAIL" not in wypis, (
        "doctor orzekł „padnięcie poza ciałem testu” o logu, w którym wiersz `FAIL` STOI "
        "— przyczyna zmyślona, nie zmierzona; wypis:\n" + wypis[-2000:])


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
