#!/usr/bin/env python3
"""Bramki wspólnej pamięci kafli OSM (6.D62).

Pamięć, której nie widać w liczbach, jest nieodróżnialna od pamięci nieistniejącej —
i to jest ta sama rodzina usterek, którą projekt tropi od 6.D27. Dlatego bramki tu
sprawdzają nie „czy plik powstał", tylko **czym jest klucz**, **co się dzieje bez
katalogu**, **czy wymuszenie naprawdę omija pamięć** i **czy oba narzędzia idą tą
samą drogą**.
"""
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import osm_tile_cache as PAMIEC  # noqa: E402
import crosscheck_alignment as CC  # noqa: E402
import surface_sections as SS  # noqa: E402

BBOX = (4.30000, 50.83000, 4.30600, 50.83600)


class _Sonda:
    """Atrapa `fetch_url`: liczy wywołania i zwraca podaną treść."""

    def __init__(self, tresc=b"<osm/>"):
        self.tresc = tresc
        self.wywolan = 0

    def __call__(self, url, expected_format=None, timeout=None):
        self.wywolan += 1
        return self.tresc, url, {}


def _z_sonda(sonda, wywolaj):
    prawdziwy = PAMIEC.P.fetch_url
    PAMIEC.P.fetch_url = sonda
    try:
        return wywolaj()
    finally:
        PAMIEC.P.fetch_url = prawdziwy


def test_klucz_jest_bboxem_i_niczym_wiecej():
    """Ten sam prostokąt to ten sam plik — także wtedy, gdy pyta drugie narzędzie.

    Cała oszczędność 6.D62 stoi na tym jednym zdaniu. Poprzednia pamięć kluczowała
    po NAZWIE OSI i kilometrażu (`{id}-{chainage}.osm`), więc ten sam prostokąt
    pytany przy innej osi schodził z sieci drugi raz.
    """
    assert PAMIEC.klucz_bboxa(BBOX) == PAMIEC.klucz_bboxa(tuple(BBOX))
    # Ta sama wartość podana z inną liczbą miejsc po przecinku niż w zapytaniu
    # (`%.5f`) MUSI dać ten sam plik — inaczej klucz byłby dokładniejszy od żądania.
    assert PAMIEC.klucz_bboxa((4.3, 50.83, 4.306, 50.836)) == PAMIEC.klucz_bboxa(BBOX)
    assert PAMIEC.klucz_bboxa((4.30001,) + BBOX[1:]) != PAMIEC.klucz_bboxa(BBOX)
    # Ujemna długość geograficzna nie ma prawa dać ścieżki wyglądającej jak opcja
    # ani wyjść z katalogu.
    nazwa = PAMIEC.klucz_bboxa((-0.5, -1.5, 4.306, 50.836))
    assert not nazwa.startswith("-") and "/" not in nazwa and ".." not in nazwa


def test_bez_katalogu_nie_ma_zadnej_pamieci():
    """`katalog=None` znaczy „bez pamięci", nie „katalog domyślny".

    **Kontrola wyrosła z pomiaru, nie z ostrożności.** W pierwszej wersji biblioteka
    brała przy `None` katalog domyślny, więc test z atrapą sieci czytał kafel
    zostawiony przez sąsiedni test: bramka `test_tiled_download_merges_a_way_that
    _arrives_from_two_tiles` zobaczyła `tiles_downloaded: 1` tam, gdzie miała
    zobaczyć 2, a w prawdziwej pamięci projektu wylądowały dwa kafle po 332 B
    z atrapy (60 plików przed zestawem, 62 po).
    """
    assert PAMIEC.sciezka(BBOX, None) is None
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)  # gdyby biblioteka sięgnęła po katalog domyślny, powstałby TUTAJ
        try:
            sonda = _Sonda()
            licznik = PAMIEC.Licznik()
            for _ in range(2):
                _z_sonda(sonda, lambda: PAMIEC.wez_kafel(BBOX, "http://x", 1.0,
                                                         katalog=None, licznik=licznik))
            assert sonda.wywolan == 2, "drugie wywołanie poszło do pamięci, choć jej nie ma"
            assert licznik.z_pamieci == 0 and licznik.pobrane == 2
            assert not os.path.exists(os.path.join(tmp, PAMIEC.DOMYSLNY_KATALOG)), (
                "biblioteka utworzyła katalog domyślny mimo `katalog=None`")
        finally:
            os.chdir(ROOT)


def test_drugie_wywolanie_nie_wychodzi_do_sieci_a_trzecie_z_wymuszeniem_wychodzi():
    """Pamięć oszczędza żądanie, a wymuszenie ją omija I NADPISUJE."""
    with tempfile.TemporaryDirectory() as tmp:
        licznik = PAMIEC.Licznik()
        pierwsza = _Sonda(b"<osm>pierwsza</osm>")
        _z_sonda(pierwsza, lambda: PAMIEC.wez_kafel(BBOX, "http://x", 1.0, tmp,
                                                    licznik=licznik))
        tresc, skad, _ = _z_sonda(pierwsza, lambda: PAMIEC.wez_kafel(
            BBOX, "http://x", 1.0, tmp, licznik=licznik))
        assert skad == "cache" and tresc == b"<osm>pierwsza</osm>"
        assert pierwsza.wywolan == 1, "drugie wywołanie mimo wszystko poszło do sieci"

        druga = _Sonda(b"<osm>druga</osm>")
        tresc, skad, _ = _z_sonda(druga, lambda: PAMIEC.wez_kafel(
            BBOX, "http://x", 1.0, tmp, wymus=True, licznik=licznik))
        assert skad == "osm-api" and tresc == b"<osm>druga</osm>"
        # Nadpisanie, nie tylko ominięcie: kolejny odczyt z pamięci ma dać NOWĄ treść.
        # Bez tej asercji „wymuszenie działa" byłoby prawdą także dla pamięci, która
        # po wymuszeniu nadal trzyma treść sprzed doby.
        tresc, skad, _ = _z_sonda(druga, lambda: PAMIEC.wez_kafel(
            BBOX, "http://x", 1.0, tmp, licznik=licznik))
        assert (skad, tresc) == ("cache", b"<osm>druga</osm>")
        assert licznik.jako_slownik() == {
            "tiles_from_cache": 2, "tiles_downloaded": 2,
            "bytes_from_cache": len(b"<osm>pierwsza</osm>") + len(b"<osm>druga</osm>"),
            "bytes_downloaded": len(b"<osm>pierwsza</osm>") + len(b"<osm>druga</osm>")}


def test_przerwany_zapis_nie_zostawia_kafla_gotowego_do_odczytu():
    """Kafel ucięty czyta się z pamięci tak samo cicho jak pełny — więc go nie ma.

    Zapis idzie przez plik tymczasowy i `os.replace`. Kontrola podkłada plik
    `.czesciowy` i żąda, żeby pamięć go NIE widziała.
    """
    with tempfile.TemporaryDirectory() as tmp:
        plik = PAMIEC.sciezka(BBOX, tmp)
        os.makedirs(tmp, exist_ok=True)
        with open(plik + ".czesciowy", "wb") as uchwyt:
            uchwyt.write(b"<osm>uciety")
        sonda = _Sonda(b"<osm>pelny</osm>")
        tresc, skad, _ = _z_sonda(sonda, lambda: PAMIEC.wez_kafel(BBOX, "http://x", 1.0, tmp))
        assert (skad, tresc) == ("osm-api", b"<osm>pelny</osm>")
        assert sonda.wywolan == 1


def test_oba_narzedzia_ida_przez_te_sama_pamiec():
    """`crosscheck_alignment` i `surface_sections` wołają TĘ SAMĄ funkcję.

    Sprawdzane zachowaniem, nie napisem w pliku: podmieniona `wez_kafel` musi
    zobaczyć wywołania z obu stron. Bramka na `import` przeszłaby dla narzędzia,
    które importuje moduł i dalej pobiera samo.
    """
    widziane = []

    def podstawiona(bbox, url, timeout, katalog=None, wymus=False, licznik=None):
        widziane.append(katalog)
        return b"<osm/>", "cache", None

    prawdziwa = PAMIEC.wez_kafel
    PAMIEC.wez_kafel = podstawiona
    try:
        CC.osm_api_ways((4.30, 50.83, 4.302, 50.832), timeout=1.0, tile_deg=0.006,
                        sleep_s=0, log=lambda *_a: None, cache_dir="KAFLE-CC")
        SS.fetch_osm_box(4.30, 50.83, 0.0012, 1.0, cache_dir="KAFLE-SS")
    finally:
        PAMIEC.wez_kafel = prawdziwa
    assert "KAFLE-CC" in widziane and "KAFLE-SS" in widziane, widziane


def test_katalog_domyslny_lezy_pod_build_bo_reguly_zabraniaja_commitowania():
    """66 MB na oś nie ma prawa trafić do repozytorium — `CLAUDE.md` §4.8."""
    assert PAMIEC.DOMYSLNY_KATALOG.split(os.sep)[0] == "build"
    gitignore = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read()
    assert any(l.strip().rstrip("/") == "build" for l in gitignore.splitlines()), (
        "`build/` nie jest ignorowane, więc katalog domyślny pamięci wszedłby do repo")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
