"""Jedno miejsce, w którym nazwa przystanku jest normalizowana przed porównaniem.

**Skąd ta potrzeba.** Z **60** unikalnych przystanków w `data/network/lines.json`
**26** ma nazwę dwujęzyczną z kreską pionową (`Arts-Loi|Kunst-Wet`, `CERIA|COOVI`,
`Étangs Noirs|Zwarte Vijvers`). Do 10.09.2026 wszystkie porównania — między osią
a linią, między dwiema liniami, między `lines.json` a GTFS — szły po CAŁYM napisie
albo po jego pierwszym członie. Zmiana samej **formy zapisu** po jednej stronie
(spacja wokół kreski, odwrotna kolejność członów, jeden człon zamiast dwóch)
rozjeżdżała kontrolę bez zmiany faktu o sieci. Dziś tego nie widać, bo obie strony
czyta się z tego samego pliku; przy pierwszym źródle zewnętrznym (GTFS, OSM) to
przestaje być prawdą.

**Kształt normalizacji jest WYPROWADZONY Z POMIARU na tych 26 nazwach, nie wymyślony**
(10.09.2026, `reports/6d111-nazwa-jako-zbior-czlonow.md`):

- separatorem jest kreska pionowa i **nie ma wokół niej spacji** w żadnej z 26 nazw —
  ale człony i tak są obcinane, bo spacja jest zmianą formy, a nie faktu;
- członów jest **dokładnie dwa** w każdej z 26 nazw i **jeden** w pozostałych 34;
  liczba nie jest jednak nigdzie zapisana jako stała, bo trzeci człon byłby nadal
  tą samą stacją;
- **żadna** z 26 nazw nie ma dwóch członów identycznych po normalizacji;
- kolejność języków **nie jest jednolita**, i to jest zmierzone wobec oficjalnego
  snapshotu GTFS (`data/network/stops.json`, pola `name_fr` i `name_nl`), a nie ocenione
  na oko: **25** nazw ma człon francuski pierwszy, a `Kraainem|Crainhem` — niderlandzki;
  nierozstrzygniętych zero. Porównanie wrażliwe na kolejność zgłaszałoby więc różnicę
  na danych, które już są w drzewie.

Stąd decyzja: **nazwa to ZBIÓR członów kanonicznych**, a dwie nazwy znaczą tę samą
stację, gdy zbiory mają część wspólną. Przecięcie, a nie równość, bo źródło zewnętrzne
ma prawo podać jeden człon tam, gdzie `lines.json` ma dwa — i odwrotnie.

**Warunek, na którym stoi przecięcie, jest zmierzony i pilnowany bramką:** 60 stacji
daje **86** członów kanonicznych i **ani jednej kolizji** — żaden człon nie należy do
dwóch różnych stacji. Gdyby należał, przecięcie sklejałoby dwie stacje w jedną, więc
`test_network_declarations.py` tego pilnuje, a nie zakłada.

**Czego ten moduł NIE robi:** nie wybiera języka wiodącego, nie tłumaczy i nie zmienia
niczego w `data/`. To są decyzje właściciela i tak mówi pole „Poza zakresem" 6.D111.
"""
import unicodedata

#: Separator członów w nazwie dwujęzycznej, tak jak stoi w `data/network/lines.json`.
SEPARATOR = "|"

#: Znaki interpunkcyjne, które w tym repozytorium różnicują ZAPIS, a nie stację:
#: feed GTFS skraca „Joséph.-Charlotte" tam, gdzie `lines.json` ma pełną nazwę
#: (`reports/przystanki-wobec-gtfs.md` §6), a apostrof stoi raz prosty, raz typograficzny.
#: Oba warianty apostrofu są tu wymienione osobno, bo `unicodedata` ich nie utożsamia:
#: `\u2019` nie jest znakiem łączącym i przez NFKD przechodzi nietknięty.
ZNAKI_ZAPISU = (".", "-", "'", "\u2019")


def kanoniczny_czlon(czlon):
    """Jeden człon bez diakrytyków, wielkimi literami, bez interpunkcji zapisu."""
    rozlozone = unicodedata.normalize("NFKD", czlon)
    bez_znakow = "".join(c for c in rozlozone if not unicodedata.combining(c))
    tekst = bez_znakow.upper()
    for znak in ZNAKI_ZAPISU:
        tekst = tekst.replace(znak, " ")
    return " ".join(tekst.split())


def czlony(nazwa):
    """Człony nazwy, obcięte, bez pustych — kolejność zachowana.

    Kolejność zachowana **mimo** że porównanie jej nie używa: człony w oryginalnej
    kolejności są potrzebne wszędzie tam, gdzie nazwa idzie do wypisu albo do klucza
    czytanego przez człowieka, a nie do porównania.
    """
    return tuple(czlon.strip() for czlon in nazwa.split(SEPARATOR) if czlon.strip())


def kanoniczna(nazwa):
    """Nazwa jako **zbiór** członów kanonicznych — postać do porównywania."""
    return frozenset(kanoniczny_czlon(czlon) for czlon in czlony(nazwa))


def ta_sama(pierwsza, druga):
    """Czy dwie nazwy znaczą tę samą stację.

    Przecięcie, nie równość: `Parc|Park` wobec `Park` to ta sama stacja zapisana
    krócej, a nie inna stacja. Pusta nazwa nie jest równa niczemu, łącznie z inną
    pustą — inaczej brak nazwy sklejałby wszystko ze wszystkim.
    """
    return bool(kanoniczna(pierwsza) & kanoniczna(druga))
