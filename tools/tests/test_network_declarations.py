#!/usr/bin/env python3
"""Deklaracje o sieci mają się zgadzać: `lines.json` ze sobą, z `docs/00` i z GTFS.

**Skąd ten moduł.** 09.09.2026 do `data/network/lines.json` dopisano Madou na linii 6
i podniesiono `stations` z 25 na 26. Przed dopisaniem zmierzono, co zobaczy zestaw,
jeżeli zrobić TYLKO połowę tej zmiany: **nic**. Plik z 26 przystankami i deklaracją
`"stations":25` przechodził 2074 testy, a `docs/00-network-data.md` z liczbą 25 obok
`lines.json` z liczbą 26 też przechodziło. Dwie liczby o tej samej rzeczy, w dwóch
plikach, i ani jednej asercji między nimi.

Cztery pierwsze bramki niżej biorą się z czterech różnych sposobów, na jakie ta
zmiana mogła wyjść krzywo. Dwie ostatnie doszły tego samego dnia, z sąsiedniego
pomiaru (`reports/simonis-elisabeth-regula-liczenia.md`): reguła liczenia stacji
60 → 59 stoi w tym samym pliku maszynowo, w `station_notes.counting_rules`,
i też nie była z niczym zestawiana. Każda bramka ma wypisaną w commicie kontrolę
negatywną.

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
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NETWORK = os.path.join(ROOT, "data", "network", "lines.json")
STOPS = os.path.join(ROOT, "data", "network", "stops.json")
DOC = os.path.join(ROOT, "docs", "00-network-data.md")

sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
import stop_names  # noqa: E402

#: Wiersz tabeli linii w `docs/00-network-data.md`:
#: `| 6 | Roi Baudouin ↔ Elisabeth | 15,5 km | 26 |`
DOC_ROW = re.compile(r"^\|\s*(\d+)\s*\|[^|]*\|\s*([\d,]+)\s*km\s*\|\s*(\d+)\s*\|\s*$",
                     re.MULTILINE)


def _network():
    with open(NETWORK, encoding="utf-8") as handle:
        return json.load(handle)


def _canonical(name):
    """Nazwa kanoniczna JEDNEGO członu — cienka nakładka na `stop_names`.

    Do 10.09.2026 stała tu własna kopia tej reguły, a `tools/track/build_alignment.py`
    miała drugą, różniącą się apostrofem. Obie strony były wewnętrznie zgodne, więc
    rozjazd nie zapalał niczego — i to jest usterka, którą zamyka 6.D111.

    Powód samej normalizacji zostaje bez zmian: feed skraca „Joséph.-Charlotte" tam,
    gdzie `lines.json` ma pełną nazwę (`reports/przystanki-wobec-gtfs.md` §6), więc
    porównanie po surowym napisie zgłaszałoby różnicę zapisu jako różnicę stacji.
    """
    return stop_names.kanoniczny_czlon(name)


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
            trafienia = [index[_canonical(czlon)]
                         for czlon in stop_names.czlony(stop)
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


def test_regula_liczenia_stacji_zgadza_sie_z_listami_i_z_deklaracja_sieci():
    """`station_notes.counting_rules` to nie notatka, tylko trzy liczby do sprawdzenia.

    Blok stoi w `lines.json` od 07.09.2026 i niesie `unique_stop_names`,
    `unique_stations` oraz `stations_incl_premetro`. Do 09.09.2026 nic ich nie
    porównywało z sąsiednimi danymi — i to nie jest teoretyczne: raport z rana
    09.09.2026 ogłosił, że „wyjaśnienia różnicy 60 → 59 w danych NIE MA", czytając
    ten sam plik i nie zaglądając do tego bloku (`reports/simonis-elisabeth-regula-liczenia.md`).
    """
    document = _network()
    rules = document["station_notes"]["counting_rules"]
    network = document["network"]
    nazwy = {stop for line in document["lines"] for stop in line["stops"]}
    assert rules["unique_stop_names"] == len(nazwy), (
        f"counting_rules mówi {rules['unique_stop_names']} unikalnych nazw, "
        f"a listy przystanków dają {len(nazwy)}")
    assert rules["unique_stations"] == network["metro_stations"], (
        f"counting_rules mówi {rules['unique_stations']} stacji, "
        f"a network.metro_stations {network['metro_stations']}")
    assert rules["stations_incl_premetro"] == network["stations_incl_premetro"], (
        f"counting_rules mówi {rules['stations_incl_premetro']} z premetrem, "
        f"a network.stations_incl_premetro {network['stations_incl_premetro']}")


def test_roznica_miedzy_liczba_nazw_a_liczba_stacji_jest_wytlumaczona_co_do_jednosci():
    """Nazw jest 60, stacji 59, a różnicę tłumaczy NAZWANY kompleks — nie prozą ogólną.

    Bez tej asercji dwie liczby wyżej mogłyby się zgadzać ze sobą i **rozjechać
    z powodem**: ktoś podnosi `unique_stop_names` razem z listą, obniża
    `unique_stations` i nigdzie nie stoi, która stacja jest liczona raz.
    Tu każda nadmiarowa nazwa musi mieć blok, który wymienia ją z nazwy.
    """
    document = _network()
    notes = document["station_notes"]
    nazwy = {stop for line in document["lines"] for stop in line["stops"]}
    roznica = notes["counting_rules"]["unique_stop_names"] - notes["counting_rules"]["unique_stations"]
    kompleksy = []
    for klucz, wartosc in notes.items():
        if klucz in ("$comment", "counting_rules") or not isinstance(wartosc, dict):
            continue
        tekst = json.dumps(wartosc, ensure_ascii=False)
        czlony = sorted(n for n in nazwy if f"'{n}'" in tekst)
        if len(czlony) >= 2:
            kompleksy.append((klucz, czlony))
    nadmiarowe = sum(len(czlony) - 1 for _klucz, czlony in kompleksy)
    assert nadmiarowe == roznica, (
        f"różnica między liczbą nazw a liczbą stacji wynosi {roznica}, a bloki "
        f"`station_notes` tłumaczą {nadmiarowe}: {kompleksy}")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.


# --- 6.D92: wspólny odcinek dwóch linii ------------------------------------------
#
# Cztery bramki wyżej pilnują liczników, powtórek, tabeli `docs/00` i przypisania
# przystanku do linii wedle GTFS. **Żadna nie porównuje dwóch linii ze sobą**, więc
# usunięcie Madou z samej L6 wraz z obniżeniem `stations` przechodziło je wszystkie.
#
# **Sformułowanie z pola „Wyjście" pozycji zostało zmierzone i jest błędne w OBIE
# strony**, dlatego bramki są dwie i inne, niż zapowiadał wpis. Brzmiało ono: „ciąg
# przystanków wspólnych dla pary linii ma być tą samą sekwencją, czytaną w jedną albo
# w drugą stronę". Zmierzone na dzisiejszym `lines.json`:
#
#   L1/L2: wspólnych  3 | ta sama kolejność: False | odwrócona: False
#   L1/L5: wspólnych 12 | ta sama kolejność: True  | odwrócona: False
#   L1/L6: wspólnych  3 | ta sama kolejność: False | odwrócona: False
#   L2/L5: wspólnych  3 | ta sama kolejność: False | odwrócona: False
#   L2/L6: wspólnych 19 | ta sama kolejność: False | odwrócona: True
#   L5/L6: wspólnych  3 | ta sama kolejność: False | odwrócona: False
#
# Cztery pary z sześciu dałyby FAŁSZYWY ALARM, bo ich część wspólna to odcinek
# Gare de l'Ouest–Beekkant PLUS osobna przesiadka Arts-Loi, leżąca gdzie indziej na
# każdej z linii. To nie jest jedna sekwencja i nie ma powodu, żeby nią była.
#
# Druga strona błędu jest gorsza: przecięcie zbiorów jest **ślepe na usunięcie**,
# którego pole „Skończone, gdy" żąda złapać. Wyrzucenie Madou z L6 wyrzuca go też
# z części wspólnej, więc obie strony porównania kurczą się zgodnie i porównanie
# przechodzi — dokładnie ta pustka, którą 6.D91 znalazło w zbiorze wyliczanym tym
# samym predykatem, który potem sprawdza.
#
# Stąd bramka pierwsza pyta o SĄSIEDZTWO, nie o sekwencję: dwa przystanki sąsiadujące
# na jednej linii i obecne na drugiej muszą sąsiadować i tam. Usunięcie Madou z L6
# czyni Arts-Loi i Botanique sąsiadami na L6, a na L2 stoi między nimi Madou — i to
# jest zgłoszenie z nazwą brakującego przystanku. Zmierzone: dziś zero naruszeń,
# po usunięciu Madou dokładnie jedno.

#: Długość jedynego maksymalnego wspólnego odcinka każdej pary linii, zmierzona
#: 10.09.2026 na `lines.json`. Nie zapadka — **zamrożony pomiar**: zmiana którejkolwiek
#: liczby znaczy, że ruszyła topologia sieci, i ma być widoczna w diffie razem
#: z powodem. Para L1/L5 (12 pozycji) nie była w treści pozycji 6.D92 wymieniona;
#: wpis znał tylko L2/L6.
WSPOLNE_ODCINKI = {
    ("L1", "L2"): 2,
    ("L1", "L5"): 12,
    ("L1", "L6"): 2,
    ("L2", "L5"): 2,
    ("L2", "L6"): 19,
    ("L5", "L6"): 2,
}


def _linie():
    return {l["id"]: l["stops"] for l in _network()["lines"]}


def wspolne_odcinki(A, B):
    """Maksymalne ciągi kolejnych przystanków `A`, które są kolejne także w `B`.

    Kierunek nie jest narzucony: odcinek biegnący w `B` pod prąd jest tak samo
    wspólnym odcinkiem — L2 i L6 dzielą pierścień czytany przeciwnie. Zwracane są
    wyłącznie ciągi co najmniej dwuprzystankowe, bo pojedyncza stacja wspólna jest
    przesiadką, a nie odcinkiem (pole „Poza zakresem" pozycji 6.D92).
    """
    pb = {s: i for i, s in enumerate(B)}
    znalezione, biezacy, kierunek = [], [], None
    for s in A:
        if s not in pb:
            if biezacy:
                znalezione.append(biezacy)
            biezacy, kierunek = [], None
            continue
        if not biezacy:
            biezacy, kierunek = [s], None
            continue
        krok = pb[s] - pb[biezacy[-1]]
        if krok in (1, -1) and kierunek in (None, krok):
            biezacy.append(s)
            kierunek = krok
        else:
            znalezione.append(biezacy)
            biezacy, kierunek = [s], None
    if biezacy:
        znalezione.append(biezacy)
    return [o for o in znalezione if len(o) >= 2]


def naruszenia_sasiedztwa(linie):
    """`[(z, na, u, w, [między])]` — pary sąsiadów z jednej linii rozdzielone na drugiej."""
    import itertools
    out = []
    for a, b in itertools.permutations(sorted(linie), 2):
        A, B = linie[a], linie[b]
        pa = {s: i for i, s in enumerate(A)}
        for u, w in zip(B, B[1:]):
            if u in pa and w in pa and abs(pa[u] - pa[w]) != 1:
                miedzy = A[min(pa[u], pa[w]) + 1:max(pa[u], pa[w])]
                out.append((b, a, u, w, miedzy))
    return out


def test_przystanek_lezacy_miedzy_sasiadami_drugiej_linii_jest_bledem():
    """Sedno 6.D92: usunięcie przystanku z JEDNEJ z dwóch linii wspólnego odcinka.

    Pytanie jest o SĄSIEDZTWO, nie o sekwencję, i to jest cała nietrywialność tej
    bramki: porównanie części wspólnej kurczy się razem z usuniętym przystankiem
    i przechodzi, a sąsiedztwo nie — przystanek zniknięty z L6 zostaje na L2 między
    dwiema stacjami, które na L6 stały się sąsiadami.
    """
    naruszenia = naruszenia_sasiedztwa(_linie())
    assert not naruszenia, (
        "przystanek stoi między dwiema stacjami, które druga linia ma obok siebie — "
        "albo brakuje go na tamtej liście, albo kolejność się rozjechała: "
        + "; ".join(f"{b} ma {u} obok {w}, a {a} wstawia między nie: "
                    + ", ".join(miedzy) for b, a, u, w, miedzy in naruszenia[:5]))


def test_wspolny_odcinek_kazdej_pary_ma_zmierzona_dlugosc():
    """Jeden maksymalny odcinek na parę, o długości z pomiaru — L2/L6 ma 19 pozycji.

    Zamrożony pomiar, nie zapadka: liczba ma się zmieniać RAZEM z topologią sieci
    i razem z powodem wpisanym w commit, a nie po cichu.
    """
    linie = _linie()
    import itertools
    zmierzone = {}
    for a, b in itertools.combinations(sorted(linie), 2):
        odcinki = wspolne_odcinki(linie[a], linie[b])
        assert len(odcinki) <= 1, (
            f"{a}/{b}: maksymalnych wspólnych odcinków jest {len(odcinki)}, a zapis "
            "zna jeden — sieć zmieniła kształt i tabela ma zostać przeliczona")
        if odcinki:
            zmierzone[(a, b)] = len(odcinki[0])
    assert zmierzone == WSPOLNE_ODCINKI, (
        f"wspólne odcinki rozjechały się z zapisem: zmierzone {zmierzone}, "
        f"zapisane {WSPOLNE_ODCINKI}")


def test_wspolny_odcinek_czyta_sie_w_obie_strony_i_zgadza_na_kazdej_pozycji():
    """Odcinek z jednej listy ma stać w drugiej jako ten sam ciąg, wprost albo wspak.

    Dla L2/L6 to jest te **19 pozycji**, których pole „Skończone, gdy" żąda porównać;
    dla L1/L5 — dwanaście, i ta para do treści pozycji nie weszła wcale.
    """
    linie = _linie()
    import itertools
    sprawdzone = 0
    for a, b in itertools.combinations(sorted(linie), 2):
        for odcinek in wspolne_odcinki(linie[a], linie[b]):
            B = linie[b]
            pb = {s: i for i, s in enumerate(B)}
            poczatek, koniec = pb[odcinek[0]], pb[odcinek[-1]]
            wycinek = B[min(poczatek, koniec):max(poczatek, koniec) + 1]
            assert wycinek == odcinek or wycinek == list(reversed(odcinek)), (
                f"{a}/{b}: wspólny odcinek czytany z {b} nie jest tym samym ciągiem: "
                f"{[s.split('|')[0] for s in wycinek]} wobec "
                f"{[s.split('|')[0] for s in odcinek]}")
            sprawdzone += len(odcinek)
    assert sprawdzone == sum(WSPOLNE_ODCINKI.values()), (
        f"porównano {sprawdzone} pozycji, a odcinki mają ich "
        f"{sum(WSPOLNE_ODCINKI.values())} — pętla przestała czegoś dotykać")


def test_przyrzad_rozpoznaje_cztery_ksztalty_i_nie_alarmuje_na_przesiadce():
    """Kontrola PRZYRZĄDU na wejściu syntetycznym, bo `data/` jest tylko do odczytu.

    Cztery kształty, każdy z osobnym trybem cichej awarii: para bez ani jednego
    wspólnego przystanku, para z JEDNĄ wspólną stacją (przesiadka — pole „Poza
    zakresem" wyklucza ją wprost), odcinek czytany wspak i wreszcie przystanek
    usunięty z jednej strony, czyli usterka, dla której ta pozycja powstała.
    """
    rozlaczne = {"A": ["a", "b", "c"], "B": ["x", "y", "z"]}
    assert wspolne_odcinki(rozlaczne["A"], rozlaczne["B"]) == [], (
        "para linii bez ani jednego wspólnego przystanku dostała wspólny odcinek")
    assert naruszenia_sasiedztwa(rozlaczne) == [], (
        "para linii bez wspólnych przystanków zgłoszona jako naruszenie sąsiedztwa")

    przesiadka = {"A": ["a", "w", "c"], "B": ["x", "w", "z"]}
    assert wspolne_odcinki(przesiadka["A"], przesiadka["B"]) == [], (
        "pojedyncza wspólna stacja policzona jako odcinek — przesiadka nim nie jest")
    assert naruszenia_sasiedztwa(przesiadka) == [], (
        "jedna wspólna stacja zgłoszona jako naruszenie sąsiedztwa — przesiadka "
        "nie mówi nic o kolejności reszty")

    wspak = {"A": ["p", "q", "r", "s"], "B": ["z", "s", "r", "q"]}
    odcinki = wspolne_odcinki(wspak["A"], wspak["B"])
    assert [len(o) for o in odcinki] == [3], (
        "odcinek trzech przystanków czytany w drugiej linii wspak nie został "
        f"rozpoznany jako jeden wspólny odcinek: {odcinki}")
    assert naruszenia_sasiedztwa(wspak) == [], (
        "odcinek biegnący wspak zgłoszony jako naruszenie sąsiedztwa")

    z_dziura = {"A": ["p", "q", "r", "s"], "B": ["z", "s", "r", "p"]}
    zgloszone = naruszenia_sasiedztwa(z_dziura)
    assert zgloszone, "przystanek wypadnięty z jednej listy nie został zgłoszony"
    assert any("q" in miedzy for *_x, miedzy in zgloszone), (
        'zgłoszenie nie nazywa brakującego przystanku, a pole \u201eSkończone, gdy\u201d '
        f'pozycji 6.D92 żąda nazwy: {zgloszone}')

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_all
    raise SystemExit(test_all.main(__file__))
