# Cztery pozycje z pomiaru — uzupełnienie kolejki (6.D61 … 6.D64)

**Zmierzone 09.09.2026 na:** `8b7b537`, kontener tej sesji.
**Przyrząd:** `tools/track/surface_sections.py`, `tools/track/crosscheck_alignment.py
--osm-source osm-api`, przejście po `.github/workflows/visual-regression.yml`
i po dwóch drogach zapasowych OSM w `tools/track/`.

---

## Dlaczego ten raport istnieje

`CLAUDE.md` §8: gdy kolejka zejdzie poniżej dwunastu pozycji, **pierwszym zadaniem
jest jej uzupełnienie**, a zadania wymyślonego na miejscu nie bierze się nigdy. Po
domknięciu 6.B26 kolejka stoi na **12**, czyli dokładnie na progu
`MINIMUM_READY_ITEMS` — następne domknięcie zeszłoby poniżej i zaczerwieniłoby
`tools/tests/test_backlog.py` w commicie, który by je zamykał.

Każda z czterech pozycji niżej ma **pomiar wykonany dziś**, plik i liczbę. Ten raport
jest miejscem, na które pola „Skąd" tych pozycji się powołują — bez niego byłyby
zadaniami wymyślonymi na miejscu, choćby brzmiały sensownie.

**Piąty kandydat został ODRZUCONY pomiarem** i to jest część wyniku: §5.

## 1. (6.D61) Zgodność źródeł w ścieżce PEŁNEGO POKRYCIA nie odsiewa portali

`tools/track/surface_sections.py` liczy zgodność UrbIS↔OSM dwiema drogami i **tylko
jedna z nich odsiewa okolice portali**, choć powód odsiewania jest w tym samym pliku
wypisany jako komentarz przy `PORTAL_HALO_M = 60.0`: „przy portalu oba źródła mają
prawo różnić się o kilkanaście metrów i taka rozbieżność **nic nie mówi** o tym, czy
odcinek biegnie w tunelu".

Ścieżka sond ma oba liczniki (`agreement_pct` i `agreement_off_portal_pct`), bo każdy
wiersz sondy niesie `range_position`. Ścieżka pełnego pokrycia (`--osm-file`, każdy
punkt osi) **nie liczy `range_position` wcale** i podaje jeden licznik, wyliczony ze
wszystkich punktów porównywalnych. Wyjście z dzisiejszego przebiegu na pakiecie D,
oba wiersze z jednego uruchomienia:

```
[POWIERZCHNIA] zgodność źródeł: 91.7% na 12 sondach; poza portalami 100.0% na 5
[POWIERZCHNIA] zgodność 75.0% na 208 punktach; OSM bez tunelu na 180 (69.8%)
```

Pierwszy wiersz mówi **dwie** liczby i różnica między nimi jest duża (91,7 % wobec
100 %). Drugi mówi jedną — i to **ta jedna** jest cytowana w `reports/surface-vs-tunnel.md`
§3 jako zgodność pakietu („D — Wschód 5 | 258 | 208 | 75,0 %"), i to na niej opiera
się zdanie o 48 punktach sprzecznych.

Ile z tych 208 punktów leży w halo portalu, **nie wiadomo** — narzędzie tego nie
liczy, więc nie da się tego dziś podać. Podanie tej liczby jest treścią pozycji.
6.B26 pokazała, że sprawa nie jest teoretyczna: najciaśniejszy łuk pakietu D leży
59,8 m od portalu według UrbIS i 14,9 m według OSM, czyli **w halo** — a mimo to
wchodzi do licznika 75,0 % na równi z punktem w środku odcinka.

## 2. (6.D62) Droga zapasowa OSM pobiera 66 MB na JEDNĄ oś i nie ma pamięci

Overpass — droga podstawowa z `docs/07-open-data-research.md` — odmawia:

```
[ŹRÓDŁO] osm: niedostępne — overpass-api.de/api/interpreter — droga PODSTAWOWA …
[KONTROLA] osm: niedostępne — <urlopen error [Errno 104] Connection reset by peer>
```

Więc każdy dzisiejszy pomiar idzie drogą zapasową, a jej koszt jest zmierzony:

```
[OSM-API] 30 kafli po 0.006°, 66137965 B pobrane, kafli odrzuconych: 0
[KONTROLA] osm: 97 way, pokrycie 100.0% (promień 50 m)
```

**66 137 965 B na jedną oś** (L5_D, najkrótszą z sześciu poza pakietem B), wobec
jednego zapytania Overpassa. Sześć osi to rząd 400 MB, a kafle **nachodzą na siebie**
między osiami: pakiety A i E przechodzą przez ten sam rejon Gare de l'Ouest, C i D
przez sąsiadujące kwadraty. Narzędzie ma `--osm-dir` jako cache **tylko dla sond**
(`fetch_osm_box`); ścieżka `osm_api_ways` w `crosscheck_alignment.py` nie ma żadnej
pamięci między przebiegami, więc powtórzenie pomiaru dla drugiej osi pobiera te same
kafle ponownie.

## 3. (6.D63) Kolor joba `visual-regression` nie odróżnia dwóch różnych zdarzeń

`.github/workflows/visual-regression.yml` ma dwa kroki, które mogą go zaczerwienić,
i **oba dają ten sam kolor**:

```
93:      - name: Run visual regression pipeline
95:        run: bash tools/ci/visual_smoke.sh
97:      - name: Upload T-012 verification artifacts
98:        if: always()
99:        uses: actions/upload-artifact@…
```

Krok 93 czerwienieje, gdy **bramka znalazła różnicę** — to wynik pomiaru i o niego
chodzi. Krok 97 czerwienieje, gdy **usługa artefaktów odmówiła przyjęcia pliku** —
i to nie jest zdanie o geometrii ani o renderze. Zmierzone 08.09.2026 na PR #415:
job wywrócił się na `403 Forbidden` przy `FinalizeArtifact`, przy odrzuconym
artefakcie **716 055 B**, podczas gdy `blender-smoke` sześć minut później wgrał
**1 905 203 B** — czyli ani limit rozmiaru, ani wyczerpana kwota. Jedno ponowienie
dało zielono, bez zmiany w kodzie.

Krok 97 nie ma `continue-on-error`, i **nie o to tu chodzi**: wyciszenie go schowałoby
prawdziwą awarię wysyłki. Chodzi o to, żeby te dwa zdarzenia dały się **rozróżnić**
z listy checków, bez czytania logu — bo bramka, która myli „znalazłem różnicę"
z „nie udało się wysłać pliku", uczy czytelnika, że jej czerwony kolor nic nie znaczy.

## 4. (6.D64) `timestamp_osm_base`: jedna droga zapasowa go ZMYŚLA, druga pomija

Pole `osm3s.timestamp_osm_base` w odpowiedzi Overpassa znaczy **stan bazy OSM**, na
którym policzono odpowiedź. Czytelnik jest jeden:

```
tools/track/crosscheck_alignment.py:398:  "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
tools/track/crosscheck_alignment.py:443:  "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
```

Pisarzy jest dwóch i **nie zgadzają się ze sobą**:

- `tools/track/fetch_osm_routes.py:167` wpisuje tam `P.utc_now_iso()`, czyli **czas
  pobrania** — pole nazwane „stan bazy OSM" niesie wtedy „kiedy to pobrałem";
- `tools/track/crosscheck_alignment.py` w `osm_api_payload()` **nie ustawia go wcale**,
  więc `osm_timestamp` jest `None` — co `reports/osm-api-droga-zapasowa.md` §wnioski
  już zauważa („droga zapasowa nie ma `timestamp_osm_base`; ma tylko daty
  poszczególnych way'ów").

Dwie drogi zapasowe do tego samego pola, dwa różne zachowania, a jedno z nich wpisuje
wartość o innym znaczeniu, niż mówi nazwa. Raport, który zacytuje `osm_timestamp`
z pierwszej drogi, poda datę pobrania jako stan bazy — i nic tego nie zatrzyma.

## 5. Piąty kandydat — ODRZUCONY POMIAREM

Miałem zapisane z 6.D54, że **idiom in-process z `test_assertion_gate.py`** dzieli
podatność zmierzoną wtedy na `test_all.py`: test wołający `sys.exit()` urywał przebieg
bez podsumowania. Sprawdzenie: **6.D54 zamknęła tę podatność u źródła.** Pętla
w `main()` ma dziś osobne `except SystemExit`, które zamienia wyjście z procesu
w FAIL testu, plus FAIL zestawu na „wykonano mniej, niż odkryto". Zagnieżdżone
wołanie `main()` w tym samym procesie nie może już zostać urwane przez sondę, więc
zgłaszanie tego byłoby zgłoszeniem naprawionej usterki.

Nie jest to strata: **kandydat odrzucony pomiarem jest tańszy niż pozycja, którą ktoś
weźmie i po godzinie stwierdzi, że nie ma czego naprawiać.** Zapisuję to tutaj, żeby
nie wrócił z notatek po raz drugi.

## 5a. Bramka złapała MOJĄ pomyłkę w tym samym commicie

Pierwsza wersja bloku 6.D64 wpisała do pola **Wejście** ścieżkę do `provenance.py`
w katalogu `tools/track/`. Moduł nazywa się `provenance`, jest importowany
w `tools/track/crosscheck_alignment.py:38` jako `import provenance as P` — i leży
w `tools/data/`, nie tam, gdzie go wpisałem. Zestaw odrzucił blok natychmiast:

```
FAIL test_no_input_field_names_a_file_outside_the_tree: pole „Wejście" nazywa plik,
którego w drzewie nie ma: ['6.D64 „Wejście": tools/track/provenance.py']
FAIL test_removing_the_field_distinction_moves_the_reported_set: ['6.D64 „Wejście": …']
```

Zapisuję to z dwóch powodów. Pierwszy: **tak wygląda działająca bramka** — kosztowała
jeden przebieg zestawu, a nie godzinę cudzej pracy nad pozycją wskazującą nieistniejący
plik. Drugi: to **nie** jest piąty przypadek wzorca z §6, i różnica jest merytoryczna.
Tam chodzi o pola nazywające pliki o związku POZORNYM — istniejące, więc dla bramki
niewidzialne. Tutaj plik po prostu nie istniał, czyli wpadłem w wariant już pilnowany.
Licznik tamtego wzorca zostaje na czterech.

**Drugi raz ta sama pomyłka, drugą bramką.** Pierwsza wersja tego akapitu wymieniła
złą ścieżkę **w grawisach**, więc zapaliła bramkę ścieżek w raportach — tę samą,
której podłogę przeliczyła 6.D58 dzień wcześniej:

```
FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie:
ścieżki, których nie ma w drzewie: ['uzupelnienie-kolejki-09-09.md:144:
tools/track/provenance.py']
```

Nie wpisałem wyjątku do `PATH_EXCEPTIONS`, bo lista wyjątków jest na pliki skasowane
i przemianowane, a nie na cytat z własnej pomyłki — zamiast tego akapit nazywa katalog
i plik osobno. Wklejone wyjścia obu bramek zostają z pełną ścieżką, bo tam są zapisem
pomiaru, a bramka czyta wyłącznie grawisy: **te same znaki w grawisach są usterką,
a w bloku wyjścia dowodem**, i ta różnica jest tu cała treść.

## 6. Czego świadomie nie zgłosiłem

- **`data/network/sources.json` nie zna warstwy `bm_urbis_topo:tunnel_line`**, choć
  `docs/07-open-data-research.md` ją opisuje, a 6.B26 z niej korzystała. Nie zgłaszam
  jako pozycji dla agenta, bo **każde jej domknięcie wymaga zapisu do `data/`**, a to
  jest decyzja właściciela (`CLAUDE.md` §4.6). Zostaje w §7 raportu 6.B26 jako
  zauważone, nie tknięte.
- **Pole „Wejście" nazywające pliki o pozornym związku** — mam cztery przypadki
  z tego tygodnia, a próg zgłoszenia ustawiłem na pięć, żeby pozycja opierała się na
  wzorcu, nie na trzech zbiegach. Licznik zostaje na czterech.
