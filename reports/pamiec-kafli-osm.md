# Wspólna pamięć kafli OSM: 66 MB → 0 B na powtórzeniu, 0 na sąsiedniej osi (6.D62)

**Zmierzone 09.09.2026 na:** `71fc13f`, kontener tej sesji, `api.openstreetmap.org`
(Overpass — droga podstawowa — nadal odmawia: `Connection reset by peer`).
**Przyrząd:** `tools/track/crosscheck_alignment.py --osm-source osm-api` na osiach
`data/track/L5_D.json` i `data/track/L6_F.json`, `tools/track/surface_sections.py`
na `L5_D`, porównanie snapshotów po `sha256` treści, `python3 tools/tests/test_all.py`.

---

## 1. Co dokładnie było zepsute

Droga zapasowa pobierała **66 137 965 B na jedną oś** (30 kafli) i nie pamiętała
niczego między przebiegami: `--osm-dir` w `surface_sections.py` był pamięcią tylko dla
sond i kluczował pliki po **nazwie osi i kilometrażu**, a `osm_api_ways`
w `crosscheck_alignment.py` nie miał pamięci wcale. Ten sam prostokąt pytany drugi raz
schodził z sieci drugi raz.

## 2. Pomiar: trzy przebiegi tej samej osi

`L5_D`, 30 kafli po 0,006°:

| przebieg | z pamięci | pobrane | czas |
|---|---|---|---|
| zimny (pamięć pusta) | 0 kafli / 0 B | **30 / 66 143 903 B** | **1 min 14,8 s** |
| ciepły | **30 / 66 143 903 B** | **0 / 0 B** | **2,6 s** |
| `--osm-refresh` | 0 / 0 B | **30 / 66 143 891 B** | 2 min 15,1 s |

Wypis, dosłownie:

```
[OSM-API] kafle: 0 z pamięci (0 B), 30 pobrane (66143903 B)
[OSM-API] kafle: 30 z pamięci (66143903 B), 0 pobrane (0 B)
[OSM-API] kafle: 0 z pamięci (0 B), 30 pobrane (66143891 B)
[OSM-API] pamięć kafli: build/osm-tiles (POMINIĘTA, --osm-refresh)
```

Drugi przebieg pobiera **zero bajtów** i jest **28,5× szybszy**.

## 3. Wynik jest ten sam co do bajtu — i to jest warunek, nie ozdoba

Snapshoty trzech przebiegów, `sha256` z kanonicznego zapisu listy `elements`:

```
zimny      12c3866f822e3fd7   58332 B   97 way
ciepły     12c3866f822e3fd7   58332 B   97 way
wymuszony  12c3866f822e3fd7   58332 B   97 way
```

Jedyny klucz różniący snapshoty to `download`, czyli **licznik pamięci** — i on ma się
różnić, bo o pamięci właśnie mówi.

**Dwanaście bajtów różnicy między przebiegiem zimnym a wymuszonym
(66 143 903 wobec 66 143 891) stoi tu, a nie jest przemilczane.** Te bajty leżą
w surowym XML poza `railway=subway`: lista `elements` jest po nich identyczna co do
haszu. Jest to dowód, że źródło **żyje** — i dokładnie z tego powodu przełącznik
wymuszający musi istnieć.

## 4. Sąsiednia oś oszczędza ZERO — i to jest wynik pomiaru, nie usterka pamięci

Pole „Skończone, gdy" zakładało, że przebieg sąsiedniej osi pobierze mniej o liczbę
wspólnych kafli. **Wspólnych kafli nie ma ani jednego.** Zmierzone dwa razy,
niezależnie:

*Z drzewa*, po wszystkich sześciu osiach pakietów:

```
L1_A 60, L1_B 44, L2_E 60, L5_C 60, L5_D 30, L6_F 30 kafli
razem 284, unikalnych 284, wspólnych dla każdej z 15 par: 0
```

**Te liczby są POPRAWIONE 09.09.2026 i poprzednie zostają wypisane, bo pomyłka była
moja i jest pouczająca.** Pierwsza wersja tego akapitu podawała „L1_A 70, L2_E 63,
razem 297" — bo skrypt liczący brał punkty osi **wprost z pliku**, a punkty w plikach
`data/track/*.json` są zapisane **względem `origin_source_crs`** i dopiero
`load_alignment` dodaje do nich początek układu. Prostokąt liczył się więc wokół
zupełnie innego miejsca, a że rozpiętość w stopniach zależy od szerokości
geograficznej, cztery osie z sześciu wyszły przypadkiem tak samo, a dwie nie.
Liczby dzisiejsze zgadzają się co do kafla z tym, co **narzędzie naprawdę pobrało**
(`tiles` w polach `download` sześciu przebiegów), i to jest jedyny powód, dla którego
wiadomo, że są prawdziwe: pomiar z drzewa został **sparowany z pomiarem z sieci**.

*Z przebiegu*: `L6_F` puszczony przy pamięci trzymającej komplet 30 kafli `L5_D`:

```
[OSM-API] kafle: 0 z pamięci (0 B), 30 pobrane (71090049 B)
```

**Przyczyna jest w kształcie siatki, nie w kluczu.** `osm_api_tiles` dzieli bbox
KONKRETNEJ osi na `nx × ny` kafli i wylicza bok z powrotem z tej liczby, żeby siatka
pokryła prostokąt dokładnie — więc granice kafli dwóch osi nie pokrywają się nigdy.
Docstring tej funkcji odrzuca wariant „stały bok, ostatni kafel wystaje" wprost:
pobierałby obszar poza bboxem, czyli obiekty, których zapytanie Overpassa nie widzi.

**Liczba dla właściciela, policzona a nie oszacowana.** Krata GLOBALNA o tym samym
boku (kafle na wielokrotnościach 0,006° od zera) dałaby dla tych samych sześciu osi:

```
żądanych 347 kafli, unikalnych 272 → 75 pobrań mniej (21,6 %)
pary dzielące kafle: L1_A↔L2_E 50, L2_E↔L5_C 8, L1_A↔L5_C 6, L1_B↔L5_D 6,
                     L2_E↔L6_F 6, L1_A↔L1_B 4, L1_A↔L5_D 2
```

(Liczby kraty globalnej poprawione tym samym rachunkiem co wyżej; poprzednia wersja
podawała „342 / 182 / 46,8 %" i wynikała z tej samej pomyłki o początek układu.
Kierunek wniosku się nie zmienia, rząd oszczędności owszem: **21,6 %, nie 46,8 %**.)

Tej zmiany **nie wprowadzam** i nie jest to ostrożność: krata globalna pokrywa obszar
poza bboxem osi, więc łamie zarówno rozstrzygnięcie z `osm_api_tiles`, jak i warunek
z tej samej pozycji — „wynik identyczny co do bajtu". Dwa warunki 6.D62 są względem
siebie **sprzeczne**, i to jest wynik pomiaru: albo kafle są wspólne między osiami,
albo wynik jest identyczny co do bajtu. Wybrałem drugi, bo jest warunkiem poprawności,
a pierwszy jest oszczędnością. Zmiana siatki to decyzja właściciela z liczbą 21,6 %
w ręku.

## 5. Drugie narzędzie idzie tą samą pamięcią

`surface_sections.py` na `L5_D` (13 sond, kwadraty 0,0012°):

```
przebieg 1   [OSM-KAFLE]  0 z pamięci (0 B), 13 pobranych (15684428 B)      17,5 s
przebieg 3   [OSM-KAFLE] 13 z pamięci (15684428 B), 0 pobranych (0 B)        2,5 s
```

Sondy obu przebiegów są **identyczne co do haszu** poza jednym polem: `osm_origin`,
które mówi `osm-api` w pierwszym i `cache` w trzecim — czyli różni się dokładnie to,
co ma się różnić.

**Przebieg 2 wypisał 4 pobrania i 1 z pamięci, i zostaje tu opisany, bo wygląda na
sprzeczność, a nią nie jest**: w tym przebiegu padł UrbIS
(`urlopen error [Errno 104] Connection reset by peer`), więc narzędzie postawiło
**5 sond zamiast 13**, w innych miejscach — inne kwadraty, inne kafle. Pamięć nie
schowała awarii źródła: licznik pokazał pobrania tam, gdzie przebieg z pamięci
pokazałby zera.

## 6. Bramki i kontrola negatywna, którą wykonał sam zestaw

Sześć bramek w `tools/tests/test_osm_tile_cache.py`. Dwie wyrosły z **pomiaru, nie
z ostrożności**:

- **`katalog=None` znaczy „bez pamięci", nie „katalog domyślny".** Pierwsza wersja
  biblioteki brała przy `None` katalog domyślny — i zestaw to złapał w tej samej
  minucie: `test_tiled_download_merges_a_way_that_arrives_from_two_tiles` zobaczył
  `tiles_downloaded: 1` zamiast 2, bo drugi kafel przyszedł z pamięci zapisanej przez
  sąsiedni test;
- **atrapa sieci zostawiała kafle w prawdziwej pamięci projektu.** Zmierzone
  policzeniem plików: **60 przed przebiegiem zestawu, 62 po** — dwa kafle po 332 B
  z atrapy. Kafel z atrapy leżący w pamięci zostałby przy następnym prawdziwym
  przebiegu wczytany tak samo cicho jak pobrany. `_run_main` podaje teraz własny
  katalog; po poprawce ten sam pomiar daje **60 przed i 60 po**.

Zapis kafla idzie przez plik tymczasowy i `os.replace`, a bramka podkłada plik
`.czesciowy` i żąda, żeby pamięć go nie widziała: kafel ucięty czyta się z pamięci
tak samo cicho jak pełny.

## 7. Czego NIE zrobiłem

**Nie zmieniłem siatki kafli** — §4, decyzja właściciela z liczbą 21,6 %.
**Nie commituję snapshotów** ani kafli: katalog domyślny to `build/osm-tiles`,
a bramka sprawdza, że `build/` jest ignorowane (`CLAUDE.md` §4.8).
**Nie tykałem** kształtu snapshotu ani Overpassa; oba stoją w polu „Poza zakresem".
**Nie mierzyłem** pozostałych czterech osi z siecią — liczba wspólnych kafli jest dla
nich policzona z drzewa, a nie z pobrania, i tak jest opisana.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py
  -> RAZEM 2098 testów, 112 modułów, kod 0

kafli w build/osm-tiles przed przebiegiem zestawu: 60, po: 60
```
