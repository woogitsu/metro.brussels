#!/usr/bin/env python3
"""Deklaracje o sieci mają się zgadzać: `lines.json` ze sobą, z `docs/00` i z GTFS.

**Skąd ten moduł.** 09.09.2026 do `data/network/lines.json` dopisano Madou na linii 6
i podniesiono `stations` z 25 na 26. Przed dopisaniem zmierzono, co zobaczy zestaw,
jeżeli zrobić TYLKO połowę tej zmiany: **nic**. Plik z 26 przystankami i deklaracją
`"stations":25` przechodził 2074 testy, a `docs/00-network-data.md` z liczbą 25 obok
`lines.json` z liczbą 26 też przechodziło. Dwie liczby o tej samej rzeczy, w dwóch
plikach, i ani jednej asercji między nimi.

Trzy bramki niżej biorą się z trzech różnych sposobów, na jakie ta zmiana mogła
wyjść krzywo, i każda ma wypisaną w commicie kontrolę negatywną.

**Czego tu świadomie NIE ma: porównania w drugą stronę.** Bramka „każdy przystanek,
który GTFS przypisuje linii, musi stać w `lines.json`" jest **zmierzona jako błędna**
(`reports/przystanki-wobec-gtfs.md` §3): oficjalny feed przypisuje linii 1 dziewięć
stacji zachodniego odgałęzienia do Erasme, czyli trasy linii 5, więc taka bramka
żądałaby dopisania do L1 dziewięciu przystanków z cudzej trasy. Kierunek zawierania
jest tu więc jednostronny i to jest wybór poparty pomiarem, nie niedokończona robota.
"""
import json
import os
import re
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NETWORK = os.path.join(ROOT, "data", "network", "lines.json")
STOPS = os.path.join(ROOT, "data", "network", "stops.json")
DOC = os.path.join(ROOT, "docs", "00-network-data.md")

#: Wiersz tabeli linii w `docs/00-network-data.md`:
#: `| 6 | Roi Baudouin ↔ Elisabeth | 15,5 km | 26 |`
DOC_ROW = re.compile(r"^\|\s*(\d+)\s*\|[^|]*\|\s*([\d,]+)\s*km\s*\|\s*(\d+)\s*\|\s*$",
                     re.MULTILINE)


def _network():
    with open(NETWORK, encoding="utf-8") as handle:
        return json.load(handle)


def _canonical(name):
    """Nazwa bez diakrytyków, wielkimi literami, bez kropek i myślników.

    Feed skraca „Joséph.-Charlotte" tam, gdzie `lines.json` ma pełną nazwę
    (`reports/przystanki-wobec-gtfs.md` §6), więc porównanie po surowym napisie
    zgłaszałoby różnicę zapisu jako różnicę stacji.
    """
    rozlozone = unicodedata.normalize("NFKD", name)
    bez_znakow = "".join(c for c in rozlozone if not unicodedata.combining(c))
    return " ".join(bez_znakow.upper().replace(".", " ").replace("-", " ")
                    .replace("'", " ").split())


def _gtfs_routes():
    """Nazwa kanoniczna -> zbiór numerów linii z oficjalnego snapshotu GTFS.

    Zwraca `None`, gdy snapshotu nie ma w drzewie — tak samo jak reszta bramek
    tego repozytorium traktuje artefakty opcjonalne.
    """
    if not os.path.isfile(STOPS):
        return None
    with open(STOPS, encoding="utf-8") as handle:
        document = json.load(handle)
    index = {}
    for station in document["stations"]:
        for nazwa in (station.get("name"), station.get("name_fr"), station.get("name_nl")):
            if nazwa:
                index.setdefault(_canonical(nazwa), set()).update(station.get("routes") or [])
    return index


def test_kazda_linia_deklaruje_tyle_przystankow_ile_ich_wypisuje():
    """`stations` obok listy `stops` to ta sama liczba zapisana dwa razy.

    Dopisanie przystanku bez podniesienia licznika (albo odwrotnie) przechodziło
    do 09.09.2026 cały zestaw — zmierzone na dopisaniu Madou do L6.
    """
    lines = _network()["lines"]
    assert lines, "lines.json nie ma ani jednej linii — bramka nie miałaby czego sprawdzić"
    niezgodne = [(l["id"], l["stations"], len(l["stops"]))
                 for l in lines if l["stations"] != len(l["stops"])]
    assert not niezgodne, (
        "linia deklaruje inną liczbę przystanków, niż wypisuje "
        f"(id, stations, len(stops)): {niezgodne}")


def test_zaden_przystanek_nie_powtarza_sie_na_tej_samej_linii():
    """Powtórka podniosłaby `len(stops)` i uciszyła bramkę wyżej bez dodania stacji."""
    powtorki = []
    for line in _network()["lines"]:
        widziane = set()
        for stop in line["stops"]:
            if stop in widziane:
                powtorki.append((line["id"], stop))
            widziane.add(stop)
    assert not powtorki, f"przystanek wypisany dwa razy na jednej linii: {powtorki}"


def test_tabela_linii_w_docs_00_zgadza_sie_z_lines_json():
    """Proza i dane trzymają te same trzy liczby — długość, liczbę stacji, numer.

    `docs/00-network-data.md` jest źródłem prawdy dla człowieka, `lines.json` dla
    narzędzi. Rozjazd między nimi jest niewidoczny dla obu.
    """
    with open(DOC, encoding="utf-8") as handle:
        wiersze = DOC_ROW.findall(handle.read())
    lines = {str(l["number"]): l for l in _network()["lines"]}
    assert len(wiersze) == len(lines), (
        f"w tabeli linii `docs/00-network-data.md` znaleziono {len(wiersze)} wierszy, "
        f"a `lines.json` ma {len(lines)} linii — jeżeli tabela zmieniła kształt, "
        "bramka przestała ją czytać i milczy zamiast pilnować")
    for numer, dlugosc, stacje in wiersze:
        assert numer in lines, f"tabela wymienia linię {numer}, której nie ma w lines.json"
        line = lines[numer]
        assert float(dlugosc.replace(",", ".")) == line["length_km"], (
            f"linia {numer}: docs/00 mówi {dlugosc} km, lines.json {line['length_km']}")
        assert int(stacje) == line["stations"], (
            f"linia {numer}: docs/00 mówi {stacje} stacji, lines.json {line['stations']}")


def test_gtfs_potwierdza_kazdy_przystanek_wypisany_na_linii():
    """Każdy przystanek z `lines.json` jest obsługiwany przez tę linię wedle GTFS.

    Kierunek jednostronny — powód stoi w docstringu modułu i jest zmierzony.
    Zawieranie w tę stronę zmierzono 09.09.2026 na wszystkich czterech liniach:
    **zero odstępstw**, razem z dopisanym tego dnia Madou (`routes=['2','6']`).
    """
    index = _gtfs_routes()
    if index is None:
        return
    nieznane, obce = [], []
    for line in _network()["lines"]:
        numer = str(line["number"])
        for stop in line["stops"]:
            trafienia = [index[_canonical(czlon)] for czlon in stop.split("|")
                         if _canonical(czlon) in index]
            if not trafienia:
                nieznane.append((line["id"], stop))
                continue
            routes = set().union(*trafienia)
            if numer not in routes:
                obce.append((line["id"], stop, sorted(routes)))
    assert not nieznane, f"nazwa z lines.json nieznana oficjalnemu GTFS: {nieznane}"
    assert not obce, (
        "GTFS nie przypisuje tego przystanku tej linii "
        f"(linia, przystanek, linie wedle GTFS): {obce}")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_all
    raise SystemExit(test_all.main(__file__))
