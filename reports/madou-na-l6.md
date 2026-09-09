# Madou dopisane do linii 6, i bramka, której brak to umożliwiał

**Zmierzone 09.09.2026 na:** `c0afb22`, kontener tej sesji.
**Przyrząd:** `data/network/lines.json`, `data/network/stops.json` (snapshot GTFS STIB
pobrany 01.09.2026, suma treści w `data/network/gtfs-manifest.json`),
`data/track/L2_E.json`, `docs/00-network-data.md`,
`tools/tests/test_network_declarations.py`, `python3 tools/tests/test_all.py`.
**Autoryzacja:** decyzja właściciela z 09.09.2026 — zgoda na tknięcie `data/`
(`CLAUDE.md` §4.6) razem z podniesieniem deklarowanej liczby przystanków L6.

---

## 1. Co zostało zmienione

Trzy liczby i jedna nazwa, w jednym commicie, bo osobno każda z nich jest fałszem:

| plik | przed | po |
|---|---|---|
| `data/network/lines.json`, `L6.stops` | 25 pozycji, między `Arts-Loi` a `Botanique` nic | 26 pozycji, `Madou` między nimi |
| `data/network/lines.json`, `L6.stations` | 25 | 26 |
| `docs/00-network-data.md`, wiersz linii 6 | `| 15,5 km | 25 |` | `| 15,5 km | 26 |` |

`network.metro_stations` **zostaje 59** i to nie jest przeoczenie: Madou już było
w sieci, na liście linii 2. Ta zmiana nie dodaje stacji, tylko przypisuje istniejącą
drugiej linii, która ją obsługuje.

## 2. Podstawa, z dwóch niezależnych źródeł oficjalnych

**GTFS STIB**, pole `routes` (numery linii, nie identyfikatory tras — sprawdzone na
stacjach o znanej przynależności w `reports/przystanki-wobec-gtfs.md` §2):

```
MADOU        routes=['2', '6']
BOTANIQUE    routes=['2', '6']
```

**Geometria shapefile'ów STIB**, oś pakietu E („Pierścień 2/6", `data/track/L2_E.json`),
gdzie Madou stoi z klasą źródła `official_stib`:

```
stop_order  5  Botanique|Kruidtuin   chainage 2606.43 m   stop_id 8421
stop_order  6  Madou                 chainage 3196.15 m   stop_id 8411
stop_order  7  Arts-Loi|Kunst-Wet    chainage 3683.46 m   stop_id 8401
```

Miejsce wstawienia wynika z tych samych danych, a nie z pamięci: lista L6 biegnie
w kierunku przeciwnym niż L2, a poza brakującym Madou obie są na wspólnym odcinku
identyczne co do pozycji. Po dopisaniu zgadzają się w całości:

```
odcinek wspólny L2 (odwrócony) vs L6[7:]: 19 pozycji, różnic: 0
```

## 3. Usterka, którą ten commit zamyka przy okazji, i ona jest ważniejsza

Przed dopisaniem **zmierzono, co zobaczy zestaw, jeżeli zrobić tylko połowę zmiany.**
Wynik:

```
plik z 26 przystankami i deklaracją "stations":25  ->  2074 testów, 110 modułów, kod 0
docs/00 z liczbą 25 obok lines.json z liczbą 26     ->  2074 testów, 110 modułów, kod 0
```

Dwie liczby o tej samej rzeczy, w dwóch plikach, i **ani jednej asercji między nimi**.
Wpis kolejki mówił o tym wprost („plik jest dziś wewnętrznie spójny i właśnie dlatego
żadna bramka tego nie widzi") — spójny był jednak tylko przypadkiem, bo spójności
nikt nie sprawdzał.

Stąd `tools/tests/test_network_declarations.py`, cztery bramki:

1. `stations` każdej linii równa się `len(stops)`;
2. żaden przystanek nie powtarza się na jednej linii — bez tego powtórka podniosłaby
   `len(stops)` i uciszyła bramkę pierwszą, nie dodając stacji;
3. tabela linii w `docs/00-network-data.md` niesie te same numery, długości i liczby
   stacji, co `lines.json`, a **zmiana kształtu tabeli jest błędem**, nie cichym
   przejściem;
4. każdy przystanek wypisany na linii jest przez tę linię obsługiwany wedle GTFS.

**Bramka czwarta jest jednostronna i to jest wybór poparty pomiarem.** Porównanie
w drugą stronę („każdy przystanek, który GTFS przypisuje linii, musi stać
w `lines.json`") jest zmierzone jako błędne w `reports/przystanki-wobec-gtfs.md` §3:
feed przypisuje linii 1 dziewięć stacji zachodniego odgałęzienia do Erasme, czyli
trasy linii 5. Taka bramka żądałaby dopisania do L1 dziewięciu przystanków z cudzej
trasy — czyli zepsucia danych, żeby uciszyć test. Kierunek zawierania zmierzono dziś
na wszystkich czterech liniach: **zero odstępstw**, razem z dopisanym Madou.

## 4. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| Madou usunięty z `L6.stops`, `stations` zostaje 26 | `FAIL test_kazda_linia_deklaruje_tyle_przystankow_ile_ich_wypisuje: [('L6', 26, 25)]`, 3/4 |
| `docs/00` zostaje przy 25, `lines.json` mówi 26 | `FAIL test_tabela_linii_w_docs_00_zgadza_sie_z_lines_json: linia 6: docs/00 mówi 25 stacji, lines.json 26`, 3/4 |
| Madou zamieniony na **duplikat** `Rogier` (obie liczby bez zmian) | `FAIL test_zaden_przystanek_nie_powtarza_sie_na_tej_samej_linii: [('L6', 'Rogier')]`, 3/4 |
| na L6 wstawiony przystanek cudzej linii (`Stockel`) | `FAIL test_gtfs_potwierdza_kazdy_przystanek_wypisany_na_linii: [('L6', 'Stockel|Stokkel', ['1'])]`, 3/4 |
| z `docs/00` znika cały wiersz linii 6 — **podmiot** bramki | `FAIL …: znaleziono 3 wierszy, a lines.json ma 4 linii — bramka przestała ją czytać i milczy zamiast pilnować`, 3/4 |

`md5sum -c` po wszystkich pięciu: `OK` dla obu plików.

Kontrola trzecia i piąta stoją tu osobno z powodu: trzecia sprawdza, że bramki nie da
się uciszyć przez podniesienie `len(stops)` czymkolwiek, a piąta — że bramka czytająca
prozę **odmawia**, gdy przestaje ją rozumieć, zamiast przechodzić na pustym dopasowaniu.
To jest rodzina 6.D65 i 6.D76: przyrząd meldujący sprawdzenie, którego nie zrobił.

## 5. Weryfikacja

```
  RAZEM 2078 testów, 111 modułów, kod 0
```

Zestaw przed pozycją: 2074 testów, 110 modułów.

## 6. Czego świadomie nie zrobiono

**Nie ruszono `network.metro_stations` ani liczby 59** — powód w §1: Madou nie jest
nową stacją sieci. Osobne pytanie „59 czy 60" jest w tym drzewie już odpowiedziane,
w bloku `station_notes.simonis_elisabeth` tego samego `lines.json`; że kolejka i raport
z rana tego bloku nie przeczytały, jest osobną pozycją i osobnym commitem.

**Nie postawiono bramki zestawiającej listy przystanków z GTFS w drugą stronę** —
powód zmierzony, §3.

**Nie tknięto `data/track/L6_F.json`.** Oś pakietu F to północna odnoga (Belgica →
Roi Baudouin, 7 stacji) i Madou na niej nie leży; wspólny pierścień jest w pakiecie E,
gdzie Madou stoi od początku.
