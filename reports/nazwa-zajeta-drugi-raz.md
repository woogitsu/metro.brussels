# Nazwa stałej zajęta drugi raz, przy innej wartości (6.B25)

**Zmierzone 06.09.2026 na commicie:** `a6463db3c83097d2c7fea460c4517f186d4507cb`
(gałąź `claude/6b25-martwa-stala`).

## 1. Stan wyjściowy

```
$ grep -rn "MIN_RADIUS_M" tools/ src/ docs/
tools/blender/clearance.py:42:MIN_RADIUS_M = 20.0
tools/tests/test_clearance_profile.py:1832:    `MIN_RADIUS_M` w tym repozytorium to 20 m, a pierścienie stoją co 5 m.
tools/tests/test_packages.py:28:MIN_RADIUS_M = 90.0
tools/tests/test_packages.py:337:        assert radii["min_m"] >= MIN_RADIUS_M, (name, radii)
```

Ta sama nazwa, **inna wartość, inne znaczenie**, obie żywe. Czytający miał dwa
sprzeczne sygnały, a trzeci plik powoływał się na tę martwą jak na obowiązującą.

## 2. Stała z `clearance.py` była martwa od pierwszego commita

Nie „przestała być czytana" — **nigdy nie była**:

```
$ git log --oneline -S "MIN_RADIUS_M" --all -- tools/blender/clearance.py
e3d9b76 Skrajnia M7 na rzeczywistych łukach pakietu A: bore_single nie ma zapasu (#50)
271b96a Skrajnia M7 na rzeczywistych łukach pakietu A: bore_single nie ma zapasu

$ git show 271b96a -- tools/blender/clearance.py | grep -n -B3 -A3 "MIN_RADIUS_M"
86-+import profiles  # noqa: E402
87-+import sweep  # noqa: E402
88-+
89:+MIN_RADIUS_M = 20.0
90-+
91-+
92-+def versine(chord_m, radius_m):
```

Wprowadzona i nietknięta. `clearance` jest importowany w siedmiu miejscach
(`profile_scan`, `profile_vehicle`, `vehicle_clearance.sh`, cztery moduły testowe),
w żadnym z nich ta nazwa nie pada; modułu nie ma też `getattr` ani `globals()`.
Usunięta.

## 3. Drugi próg nie został przemianowany — przestał być kopią

Wpis kolejki proponował **przemianowanie** `MIN_RADIUS_M` w `test_packages.py`, żeby
nazwa mówiła, czego dotyczy. Pomiar pokazał lepsze wyjście: nad tymi trzema liczbami
stał komentarz

```python
# Granice z tools/track/validate.py — oś, która ich nie spełnia, nie przejdzie walidatora.
MAX_POINT_GAP_M = 25.0
MIN_POINT_GAP_M = 0.5
MIN_RADIUS_M = 90.0
```

czyli **kopia** `validate.LIMITS`, z komentarzem mówiącym, skąd jest, i bez niczego,
co pilnowałoby, żeby nadal stamtąd była. Kopia progu walidatora rozjeżdża się w jedną
stronę **po cichu**: oś, która przestaje spełniać prawdziwy próg, przechodzi ten test,
bo tutejszy został przy starej wartości. Przemianowanie zostawiłoby tę usterkę
nietkniętą, tylko pod ładniejszą nazwą.

Trzy liczby zastąpione jednym `VALIDATOR = V.LIMITS` i czytane po kluczu. Nazwa
`MIN_RADIUS_M` znika przy okazji — kolizja z §1 przestaje istnieć, bo drugiej definicji
nie ma, a nie dlatego, że nazwano ją inaczej.

**Wartości nie zmieniono** — pole „Poza zakresem" tej pozycji wyklucza zmianę progu
90 m i tak zostaje. Zmieniło się wyłącznie to, skąd liczba pochodzi.

## 4. Docstring powoływał się na liczbę słabszą, niż obowiązuje

`test_clearance_profile.py:1832` uzasadniał równoważność mutacji zdaniem:
„`MIN_RADIUS_M` w tym repozytorium to 20 m, a pierścienie stoją co 5 m". Nie tylko
powoływał się na stałą martwą — powoływał się na **słabszą** granicę, niż obowiązuje.
Najmniejszy dopuszczalny promień to `LIMITS["min_radius_m"]`, czyli **90 m**, i 90 m
tym bardziej wyklucza zdegenerowany łuk (R = 0,01 m) niż 20 m. Argument jest po tej
zmianie mocniejszy, nie słabszy. Zdanie przepisane, nie dopisane obok.

## 5. Bramka: kolizja przechodzi tylko z uzasadnieniem

Pole „Skończone, gdy" mówiło: „w repozytorium nie ma dwóch stałych o tej samej nazwie
i różnych wartościach". **Pomiar pokazał, że tego kryterium nie należy spełniać.**

```
stalych modulowych o wartosci prostej: 232
nazw z ROZNYMI wartosciami w co najmniej dwoch plikach: 5
  DEFAULT_SOURCE_ID   fetch_gtfs.py='stib_gtfs'      fetch_stib_shapes.py='stib_shapefiles'
  MIN_RADIUS_M        clearance.py=20.0              test_packages.py=90.0
  SOURCE_CRS          build_alignment.py='EPSG:31370' inspire_rail.py='EPSG:3035'
  SOURCE_ID           fetch_osm_routes.py='openstreetmap'  inspire_rail.py='belgian_mobility_inspire_rails'
                      tunnel_width.py='brussels_mobility_metro'
  TOLERANCE_M         glb_report.py=0.01  m7_report.py=0.001  test_platform_length_in_pipeline.py=0.001
```

**Cztery z pięciu są poprawne.** `SOURCE_ID`, `DEFAULT_SOURCE_ID` i `SOURCE_CRS` to
tożsamość modułu — każdy pobieracz **ma** mieć własną, wspólna wartość byłaby błędem
(scaliłaby OSM, INSPIRE i Brussels Mobility w jeden rejestr proweniencji, a Lambert 72
z ETRS89-LAEA w jeden układ źródłowy). `TOLERANCE_M` różni się tym, czego dotyczy
pomiar. Reguła „żadnych powtórzonych nazw" zapaliłaby się na czterech przypadkach
zrobionych dobrze i zostałaby wyłączona w tydzień.

Dlatego `tools/tests/test_constant_names.py` jest **zapadką z uzasadnieniami**: kolizja
przechodzi wtedy i tylko wtedy, gdy stoi na liście z jednozdaniowym powodem, dopisanym
w tym samym commicie. Pilnowane są oba kierunki — wpis, który przestał opisywać
kolizję, też zapala bramkę, bo gnijąca lista wyjątków jest gorsza od jej braku:
wygląda na przemyślaną.

## 6. Kontrole negatywne — WYKONANE, cztery

| | co zepsute | wynik |
|---|---|---|
| KN-1 | martwa stała wraca do `clearance.py` | **nic nie padło** — patrz niżej |
| KN-2 | `MIN_RADIUS_M` wpisany na listę wyjątków, obie definicje przywrócone | `FAIL test_the_name_from_this_task_is_gone` + `FAIL test_the_package_limits_are_read_from_the_validator_not_copied` |
| KN-3 | wpis na liście bez kolizji | `FAIL test_no_justification_outlives_the_clash_it_describes: UZASADNIONE opisuje kolizje, ktorych juz nie ma: NIE_MA_TAKIEJ_KOLIZJI` |
| KN-4 | próg walidatora przepisany z powrotem jako `>= 90.0` | `FAIL test_the_package_limits_are_read_from_the_validator_not_copied: prog min_radius_m nie jest brany z walidatora` |

**KN-1 nie zapala bramki i to jest jej zmierzona granica, nie przeoczenie.** Sama
stała `MIN_RADIUS_M = 20.0` przywrócona do `clearance.py` **nie tworzy kolizji** — po
§3 druga definicja nie istnieje, więc nazwa jest w repozytorium jedna. Ta bramka łapie
**kolizję**, nie **martwotę**. Gdyby raport pominął KN-1, wyglądałoby to na komplet.

Czy bramka na martwotę jest wykonalna, zostało zmierzone, a nie założone:

```
stalych modulowych (WIELKIE): 696
nieczytanych nigdzie w tools/ i src/: 1
   tools/track/normalize_stops.py LOCATION_STATION
z tego wystepujacych w *.sh lub .github/: 0
```

Jeden wyjątek, i **uzasadniony**: `LOCATION_STATION = "1"` stoi w trójce
`LOCATION_STOP` / `LOCATION_STATION` / `LOCATION_ENTRANCE`, która spisuje wyliczenie
`location_type` z GTFS. Dwie wartości są czytane, trzecia nie — usunięcie jej
zepsułoby czytelność zbioru, a nie usunęło ciężaru. Bramka na martwotę jest więc
wykonalna dziś, z listą wyjątków o jednym wpisie; jest w kolejce jako **6.B29**,
osobno, bo to inna bramka niż ta z §5, a nie jej rozszerzenie.

## 7. Weryfikacja

```
$ grep -rn "MIN_RADIUS_M" tools/ src/ docs/ | grep -v "^docs/TASKS.md" | grep -v __pycache__
tools/tests/test_clearance_profile.py:1836:    się na `MIN_RADIUS_M` „w tym repozytorium" równe 20 m — stałą z
tools/tests/test_packages.py:31:#: Nazwa `MIN_RADIUS_M` znika przy okazji — była w repozytorium zajęta drugi raz,
tools/tests/test_constant_names.py:4:**Skad ta bramka.** 6.B25. `MIN_RADIUS_M` istnialo w repozytorium dwa razy: 20,0
tools/tests/test_constant_names.py:115:    """`MIN_RADIUS_M` bylo powodem tej bramki i ma NIE wrocic pod dwiema wartosciami.
tools/tests/test_constant_names.py:121:    assert "MIN_RADIUS_M" not in UZASADNIONE, (
tools/tests/test_constant_names.py:122:        "MIN_RADIUS_M zostal wpisany na liste uzasadnionych kolizji — 6.B25 zmierzylo, "
tools/tests/test_constant_names.py:125:    assert "MIN_RADIUS_M" not in kolizje(), (
tools/tests/test_constant_names.py:126:        "MIN_RADIUS_M znowu ma dwie wartosci w repozytorium")
tools/tests/test_constant_names.py:145:    for przepisana in ("MIN_RADIUS_M = ", "MIN_POINT_GAP_M = ", "MAX_POINT_GAP_M = "):
```

Trafień jest dziewięć i **ani jedno nie jest definicją stałej**. Dwa pierwsze to proza
mówiąca, że tej stałej nie ma; siedem pozostałych to bramka z §5, której zadaniem jest
pilnować, żeby nie wróciła — nazwa musi w niej padać, żeby ją rozpoznała. Liczba
definicji i liczba odczytów jest tu jedyną, która coś znaczy, i obie wynoszą **zero**:

```
$ grep -rn "^MIN_RADIUS_M *=" tools/ src/ ; echo "definicji: $?"
definicji: 1        # kod 1 = grep nie znalazł ani jednego wiersza
```

```
$ python3 tools/tests/test_all.py
  RAZEM 66.880 s, 1786 testów, 91 modułów
kod: 0
```

## 8. Czego świadomie nie zrobiono

- **Bramki na stałą nieczytaną** — §6. Zmierzona jako wykonalna, w kolejce jako 6.B29;
  osobna bramka, nie rozszerzenie tej z §5.
- **Usunięcia `LOCATION_STATION`** — §6. To nie jest ciężar, tylko brakujący element
  wyliczenia GTFS, i jego usunięcie pogorszyłoby plik.
- **Zmiany wartości progu 90 m** — pole „Poza zakresem" pozycji. Zmieniło się źródło
  liczby, nie liczba.
- **Ujednolicenia `TOLERANCE_M`** — §5. Trzy różne tolerancje trzech różnych pomiarów;
  wspólna wartość byłaby regresem, nie porządkiem.
