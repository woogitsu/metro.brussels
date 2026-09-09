#!/usr/bin/env python3
"""Wspólna pamięć kafli OSM dla obu narzędzi sięgających po `/api/0.6/map` (6.D62).

Po co. Overpass — droga podstawowa z `docs/07-open-data-research.md` — bywa
nieosiągalny, więc pomiar schodzi na drogę zapasową: surowe API OSM, kafel po kaflu.
Zmierzone 09.09.2026: **66 137 965 B na jedną oś** przy 30 kaflach, a `--osm-dir`
w `tools/track/surface_sections.py` był pamięcią WYŁĄCZNIE dla sond i kluczował pliki
po **nazwie osi i kilometrażu**, więc ten sam prostokąt pobierany przy innej osi albo
przez `tools/track/crosscheck_alignment.py` schodził z sieci drugi raz.

Klucz jest tu **bboxem kafla i niczym więcej** — dwa narzędzia pytające o ten sam
prostokąt trafiają w ten sam plik. Katalog domyślny leży pod `build/`, bo `CLAUDE.md`
§4.8 zabrania commitowania takich plików, a 66 MB na oś jest dokładnie tym, czego ten
zakaz dotyczy.

Czego ta pamięć NIE robi i to jest zmierzone, nie przeoczone: **nie oszczędza ani
jednego kafla MIĘDZY OSIAMI**. Siatka kafli powstaje z podziału bboxa KONKRETNEJ osi
(`osm_api_tiles`), więc kafle dwóch osi nie pokrywają się nigdy — sprawdzone na
wszystkich sześciu osiach pakietów: **297 kafli, 297 unikalnych, zero wspólnych dla
każdej z piętnastu par**. Liczba dla porównania i dla właściciela: krata GLOBALNA
o tym samym boku dałaby 342 kafle żądane i 182 unikalne, czyli 160 pobrań mniej
(46,8 %) — ale pokrywałaby obszar POZA bboxem osi, co `osm_api_tiles` odrzuca wprost
i co złamałoby warunek „wynik identyczny co do bajtu". Zmiana siatki jest więc
decyzją właściciela, a nie skutkiem ubocznym pamięci. Pomiar:
`reports/pamiec-kafli-osm.md`.
"""
import os

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
import provenance as P  # noqa: E402

#: Katalog domyślny. Pod `build/`, nie w repozytorium — reguła 8 `CLAUDE.md`.
DOMYSLNY_KATALOG = os.path.join("build", "osm-tiles")

#: Ile miejsc po przecinku wchodzi do klucza. TA SAMA precyzja, z jaką oba narzędzia
#: budują `bbox=` w zapytaniu (`%.5f`), więc klucz nie potrafi być dokładniejszy
#: od żądania: dwa bboxy dające to samo zapytanie MUSZĄ dać ten sam plik.
MIEJSC = 5


def klucz_bboxa(bbox):
    """Nazwa pliku dla prostokąta `(west, south, east, north)`.

    Czytelna, nie skrót skrótu: przy 300 plikach w katalogu człowiek ma poznać,
    którego kafla brakuje, bez rozwijania hasza.
    """
    west, south, east, north = (round(float(v), MIEJSC) for v in bbox)
    return ("w%.5f_s%.5f_e%.5f_n%.5f.osm" % (west, south, east, north)).replace("-", "m")


class Licznik:
    """Ile kafli przyszło z pamięci, a ile z sieci — i ile to bajtów.

    Liczy OSOBNO bajty z pamięci i z sieci, bo zdanie „cache działa" bez tych dwóch
    liczb jest nieodróżnialne od „cache nie jest wołany", a to jest ta sama rodzina
    usterek, którą projekt tropi od 6.D27.
    """

    def __init__(self):
        self.z_pamieci = 0
        self.pobrane = 0
        self.bajty_z_pamieci = 0
        self.bajty_pobrane = 0

    def jako_slownik(self):
        return {"tiles_from_cache": self.z_pamieci, "tiles_downloaded": self.pobrane,
                "bytes_from_cache": self.bajty_z_pamieci,
                "bytes_downloaded": self.bajty_pobrane}

    def __str__(self):
        return (f"kafle: {self.z_pamieci} z pamięci ({self.bajty_z_pamieci} B), "
                f"{self.pobrane} pobrane ({self.bajty_pobrane} B)")


def sciezka(bbox, katalog):
    """Ścieżka pliku kafla. `katalog` pusty znaczy „bez pamięci", nie „domyślny".

    Tego rozróżnienia nie było w pierwszej wersji i **zapaliło bramkę**: przy
    `katalog=None` funkcja brała `DOMYSLNY_KATALOG`, więc test z atrapą sieci
    czytał kafel zapisany na dysku przez sąsiedni test i widział `tiles_downloaded: 1`
    tam, gdzie miał zobaczyć 2. Katalog domyślny należy do **wiersza poleceń**,
    nie do biblioteki: wołający, który o pamięć nie prosił, ma jej nie dostać.
    """
    if not katalog:
        return None
    return os.path.join(katalog, klucz_bboxa(bbox))


def wez_kafel(bbox, url, timeout, katalog=None, wymus=False, licznik=None):
    """`(zawartość, skąd, powód)` — `skąd` to `cache` albo `osm-api`.

    `wymus` omija pamięć i **nadpisuje** ją świeżą odpowiedzią. Bez tego przełącznika
    pamięć byłaby gorsza od jej braku w dniu, w którym OSM się zmieni: nie dałoby się
    jej ominąć inaczej niż kasowaniem plików z ręki.
    """
    plik = sciezka(bbox, katalog)
    if plik and not wymus and os.path.isfile(plik):
        with open(plik, "rb") as uchwyt:
            zawartosc = uchwyt.read()
        if licznik is not None:
            licznik.z_pamieci += 1
            licznik.bajty_z_pamieci += len(zawartosc)
        return zawartosc, "cache", None
    try:
        zawartosc, _url, _naglowki = P.fetch_url(url, expected_format="xml", timeout=timeout)
    except Exception as blad:  # niedostępność jest wynikiem, nie powodem do pominięcia
        return None, "niedostępne", str(blad)
    if plik:
        os.makedirs(os.path.dirname(plik) or ".", exist_ok=True)
        # Zapis przez plik tymczasowy i `replace`: przerwany przebieg zostawiłby
        # inaczej kafel UCIĘTY, a ucięty czyta się z pamięci tak samo cicho jak pełny.
        tymczasowy = plik + ".czesciowy"
        with open(tymczasowy, "wb") as uchwyt:
            uchwyt.write(zawartosc)
        os.replace(tymczasowy, plik)
    if licznik is not None:
        licznik.pobrane += 1
        licznik.bajty_pobrane += len(zawartosc)
    return zawartosc, "osm-api", None
