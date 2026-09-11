#!/usr/bin/env python3
"""Cztery kopie liczby 170 000 i rola każdej — 6.D138.

**Dlaczego OSOBNY moduł, a nie `test_braking.py`, gdzie stoi porównanie ze źródłem.**
Te testy kopiują drzewo i URUCHAMIAJĄ w nim `test_all.py test_braking.py`. Gdyby
mieszkały w jednym z tych dwóch modułów, kopia zawierałaby je także — i uruchamiałaby
kolejną kopię, bez końca. Zmierzone tu, nie przewidziane: pierwsza wersja stała
w `test_braking.py` i przebieg **nie skończył się** w 300 s, po czym został ubity.
Ta sama pułapka co przy 6.D122 i 6.D114, i ten sam wniosek: **drzewo probne nie może
zawierać testu, który je buduje.**

Moduł nie mierzy fizyki hamowania ani rejestru — mierzy **podział pracy między
czterema kopiami jednej liczby**, więc własne miejsce ma także z tego powodu.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))


#: **Cztery kopie liczby 170 000 i rola każdej — 6.D138.** Rozstrzygnięcie stoi tutaj
#: w całości; przy pinie w `test_all.py` powtórzona jest sama tabela ról, bo tam ktoś
#: czyta asercję i ma od razu wiedzieć, czego ona NIE sprawdza.
#:
#:   1. `data/vehicle/m7-spec.json`  ŹRÓDŁO, z `source_id` i `approximate: true`
#:   2. `tools/physics/reference.py` DRUGA DROGA — literał jest treścią tablicy
#:   3. `test_all.py`, pin masy      PIN na kopii 2
#:   4. `test_m7_spec_registry_provenance`  PIN na kopii 1
#:
#: **Zmierzone 11.09.2026 na kopii roboczej drzewa, bez zmiany `data/`:** podmiana
#: w rejestrze zapala **4** testy z 2346 i pinu z `test_all.py` NIE ma wśród nich;
#: podmiana w referencji zapala **6** i pin jest wśród nich. Testy niżej wykonują obie
#: połowy tego pomiaru na DWÓCH modułach zamiast na całym zestawie — cały moduł chodzi
#: **2,1 s** wobec 170 s przebiegu pełnego — więc zbiory nazw są tam mniejsze niż 4 i 6,
#: i o to chodzi: mierzone jest, KTÓRY test się zapala, a nie ile ich razem.
#: **Zbiory zmierzone 11.09.2026 na dwóch modułach (`test_all.py test_braking.py`),
#: a nie na całym zestawie.** Porównanie jest RÓWNOŚCIĄ, nie zawieraniem, i to jest
#: wybór po kontroli, która wyszła ZIELONA: KN-5 zdjęła `docs/` i `reports/` z drzewa
#: probnego, a testy pytające tylko „czy nazwa X jest w zbiorze" przeszły, choć zbiór
#: urósł o dwa testy padające na brakujących plikach. Równość pilnuje CAŁEGO podziału
#: pracy, czyli tego, o co pozycja pytała.
PADAJA_NA_ZMIANE_REJESTRU = {
    "test_ile_parametrow_modelu_jest_PRZYBLIZONYCH",
    "test_m7_spec_registry_provenance",
    "test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM",
    "test_wypis_modelu_NAZYWA_parametry_przyblizone",
}

PADAJA_NA_ZMIANE_REFERENCJI = {
    "test_m7_reference_mass_pin_has_not_drifted",
    "test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM",
}

KOPIE_170000 = {
    "źródło": "data/vehicle/m7-spec.json",
    "druga droga": "tools/physics/reference.py",
}


def _drzewo_probne(katalog, podmiana):
    """Kopia `tools/`, `data/`, `docs/` i `reports/` z jedną podmienioną liczbą.

    Kopia, a nie drzewo robocze: `data/` jest tylko do odczytu (`CLAUDE.md` §4.6),
    a kontrola negatywna nie jest od tego wyjątkiem. Cztery katalogi, bo moduły
    czytają też dokument audytu i raport hamowania — bez nich w wypisie pojawia się
    szum, który trzeba by odsiewać nazwami.
    """
    import shutil

    for nazwa in ("tools", "data", "docs", "reports"):
        shutil.copytree(os.path.join(ROOT, nazwa), os.path.join(katalog, nazwa),
                        ignore=shutil.ignore_patterns("__pycache__"))
    podmiana(katalog)
    return katalog


def _padly(katalog, moduly):
    """Nazwy testów, które padły w drzewie probnym. Przebieg podprocesem."""
    import subprocess

    wynik = subprocess.run(
        [sys.executable, os.path.join(katalog, "tools", "tests", "test_all.py")] + moduly,
        capture_output=True, text=True, cwd=katalog)
    return {w.split(":")[0].split()[-1]
            for w in wynik.stdout.splitlines() if w.strip().startswith("FAIL")}


def test_pin_referencji_milczy_na_zmianie_rejestru_a_porownanie_ze_zrodlem_nie():
    """**Sedno 6.D138, wykonane jako pomiar, nie opisane.**

    Pin w `test_all.py` porównuje kopię z literałem, więc na zmianie ŹRÓDŁA milczy —
    i to jest jego rola, nie usterka. Usterką było jego dawne imię
    (`test_m7_reference_uses_source_backed_aw0`), obiecujące sprawdzenie oparcia
    o źródło, którego ta asercja nie robi.
    """
    import json as _json
    import tempfile

    def zmien_rejestr(katalog):
        sciezka = os.path.join(katalog, "data", "vehicle", "m7-spec.json")
        with open(sciezka, encoding="utf-8") as uchwyt:
            dane = _json.load(uchwyt)
        dane["parameters"]["empty_mass_kg"]["value"] = 171000.0
        with open(sciezka, "w", encoding="utf-8") as uchwyt:
            _json.dump(dane, uchwyt, ensure_ascii=False, indent=1)

    with tempfile.TemporaryDirectory(prefix="metro-170000-") as katalog:
        _drzewo_probne(katalog, zmien_rejestr)
        padly = _padly(katalog, ["test_all.py", "test_braking.py"])

    assert padly == PADAJA_NA_ZMIANE_REJESTRU, (
        "zmiana ŹRÓDŁA zapala inny zbiór testów niż zmierzony: doszło %s, ubyło %s"
        % (sorted(padly - PADAJA_NA_ZMIANE_REJESTRU),
           sorted(PADAJA_NA_ZMIANE_REJESTRU - padly)))
    assert "test_m7_reference_mass_pin_has_not_drifted" not in padly, (
        "pin tablicy referencyjnej zapalił się na zmianie REJESTRU — porównuje "
        "literał z literałem, więc nie ma prawa: %s" % sorted(padly))


def test_pin_referencji_ZAPALA_sie_na_zmianie_samej_referencji():
    """Druga połowa: pin jest pinem, a nie ozdobą.

    Bez tej połowy zdanie „pin milczy na zmianie rejestru" czytałoby się jak zarzut,
    a jest opisem podziału pracy: od rozjazdu ze źródłem jest inny test.
    """
    import tempfile

    def zmien_referencje(katalog):
        sciezka = os.path.join(katalog, "tools", "physics", "reference.py")
        with open(sciezka, encoding="utf-8") as uchwyt:
            tekst = uchwyt.read()
        nowy = tekst.replace('"AW0":170000.0', '"AW0":171000.0', 1)
        assert nowy != tekst, "podmiana literału w `reference.py` nie trafiła"
        with open(sciezka, "w", encoding="utf-8") as uchwyt:
            uchwyt.write(nowy)

    with tempfile.TemporaryDirectory(prefix="metro-170000-") as katalog:
        _drzewo_probne(katalog, zmien_referencje)
        padly = _padly(katalog, ["test_all.py", "test_braking.py"])

    assert padly == PADAJA_NA_ZMIANE_REFERENCJI, (
        "zmiana REFERENCJI zapala inny zbiór testów niż zmierzony: doszło %s, ubyło %s"
        % (sorted(padly - PADAJA_NA_ZMIANE_REFERENCJI),
           sorted(PADAJA_NA_ZMIANE_REFERENCJI - padly)))
    assert "test_m7_spec_registry_provenance" not in padly, (
        "pin na ŹRÓDLE zapalił się na zmianie referencji — mierzy wtedy nie to, "
        "co opisuje: %s" % sorted(padly))

    # Dwa zbiory różnią się o TRZY nazwy i przecinają w JEDNEJ — to jest podział
    # pracy, o który pozycja pytała, wypisany liczbą zamiast prozą.
    wspolne = PADAJA_NA_ZMIANE_REJESTRU & PADAJA_NA_ZMIANE_REFERENCJI
    assert wspolne == {"test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM"}, (
        "wspólną częścią obu zbiorów miał być JEDEN test — ten, który porównuje "
        "kopię ze źródłem: %s" % sorted(wspolne))


def test_kazda_z_dwoch_kopii_liczby_naprawde_lezy_tam_gdzie_mowi_opis():
    """Role z komentarza wyżej sprawdzone na drzewie, a nie przyjęte na słowo."""
    zrodlo = os.path.join(ROOT, KOPIE_170000["źródło"])
    with open(zrodlo, encoding="utf-8") as uchwyt:
        import json as _json
        dane = _json.load(uchwyt)
    assert dane["parameters"]["empty_mass_kg"]["value"] == 170000.0, (
        "źródło podaje %r" % dane["parameters"]["empty_mass_kg"]["value"])

    referencja = os.path.join(ROOT, KOPIE_170000["druga droga"])
    with open(referencja, encoding="utf-8") as uchwyt:
        tekst = uchwyt.read()
    assert '"AW0":170000.0' in tekst, (
        "tablica referencyjna nie niesie już literału masy AW0 — jeśli zaczęła "
        "czytać rejestr, DRUGA DROGA zniknęła i porównanie C# z Pythonem stoi "
        "na jednej kopii")



# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))
    import test_all
    raise SystemExit(test_all.main(__file__))
